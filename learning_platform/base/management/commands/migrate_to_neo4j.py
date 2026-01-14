"""
Command Django pour migrer les données de SQLite vers Neo4j
Usage: python manage.py migrate_to_neo4j [--dry-run] [--execute] [--verbose]
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from neomodel import db, config
from django.conf import settings
import logging

logger = logging.getLogger('base')


class Command(BaseCommand):
    help = 'Migre les données de SQLite vers Neo4j'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les opérations sans les exécuter'
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Exécute réellement la migration'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche les détails'
        )
        parser.add_argument(
            '--skip-clean',
            action='store_true',
            help='Ne pas nettoyer Neo4j avant migration'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        execute = options['execute']
        verbose = options['verbose']
        skip_clean = options['skip_clean']

        if not dry_run and not execute:
            self.stdout.write(self.style.ERROR(
                'Vous devez spécifier --dry-run ou --execute'
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'MIGRATION SQLite → Neo4j\n'
            f'Mode: {"DRY RUN (simulation)" if dry_run else "EXÉCUTION RÉELLE"}\n'
            f'{"="*60}\n'
        ))

        # Configurer neomodel
        config.DATABASE_URL = settings.NEOMODEL_NEO4J_BOLT_URL

        if execute and not dry_run:
            confirm = input('⚠️  Êtes-vous sûr de vouloir migrer? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write('Migration annulée.')
                return

        try:
            # Importer les modèles Neo4j
            from base.neo_models import (
                NeoUser, NeoCourse, NeoModule, NeoResource,
                NeoEvaluation, NeoQuestion
            )
            
            # Importer les modèles Django
            from base.models import (
                Course, Module, Resource, Evaluation, Question,
                Enrollment, Submission, SubmittedAnswer, ResourceView
            )

            # Étape 0: Nettoyer Neo4j
            if execute and not skip_clean:
                self.stdout.write('\n🧹 Nettoyage de Neo4j...')
                db.cypher_query("MATCH (n) DETACH DELETE n")
                self.stdout.write(self.style.SUCCESS('✅ Neo4j nettoyé'))

            # Étape 1: Migrer les Users
            self.migrate_users(dry_run, verbose, NeoUser)

            # Étape 2: Migrer les Courses
            self.migrate_courses(dry_run, verbose, NeoUser, NeoCourse)

            # Étape 3: Migrer les Modules
            self.migrate_modules(dry_run, verbose, NeoCourse, NeoModule, Module)

            # Étape 4: Migrer les Resources
            self.migrate_resources(dry_run, verbose, NeoModule, NeoResource, Resource)

            # Étape 5: Migrer les Evaluations
            self.migrate_evaluations(dry_run, verbose, NeoModule, NeoEvaluation, Evaluation)

            # Étape 6: Migrer les Questions
            self.migrate_questions(dry_run, verbose, NeoEvaluation, NeoQuestion, Question)

            # Étape 7: Migrer les Enrollments
            self.migrate_enrollments(dry_run, verbose, NeoUser, NeoCourse, Enrollment)

            # Étape 8: Migrer les Submissions
            self.migrate_submissions(dry_run, verbose, NeoUser, NeoEvaluation, Submission)

            # Étape 9: Migrer les Resource Views
            self.migrate_resource_views(dry_run, verbose, NeoUser, NeoResource, ResourceView)

            # Étape 10: Vérification
            if not dry_run:
                self.verify_migration()

            self.stdout.write(self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'✅ MIGRATION TERMINÉE\n'
                f'{"="*60}\n'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERREUR: {str(e)}'))
            logger.error(f'Migration error: {str(e)}', exc_info=True)
            raise

    def migrate_users(self, dry_run, verbose, NeoUser):
        """Migrer les utilisateurs Django vers Neo4j"""
        User = get_user_model()
        users = User.objects.all()
        
        self.stdout.write(f'\n👤 Users: {users.count()} à migrer')
        
        if dry_run:
            for user in users[:5]:
                self.stdout.write(f'   - {user.username} ({getattr(user, "role", "User")})')
            if users.count() > 5:
                self.stdout.write(f'   ... et {users.count() - 5} autres')
            return

        count = 0
        for user in users:
            try:
                neo_user = NeoUser(
                    username=user.username,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=getattr(user, 'role', 'Student'),
                    date_joined=user.date_joined,
                    is_active=user.is_active,
                    is_staff=user.is_staff
                ).save()
                count += 1
                if verbose:
                    self.stdout.write(f'   ✓ {user.username}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ {user.username}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ {count}/{users.count()} users migrés'))

    def migrate_courses(self, dry_run, verbose, NeoUser, NeoCourse):
        """Migrer les cours"""
        from base.models import Course
        courses = Course.objects.all()
        
        self.stdout.write(f'\n📚 Courses: {courses.count()} à migrer')
        
        if dry_run:
            for course in courses[:5]:
                self.stdout.write(f'   - {course.title}')
            return

        count = 0
        for course in courses:
            try:
                neo_course = NeoCourse(
                    title=course.title,
                    description=course.description or '',
                    level=course.level or 'Beginner',
                    estimated_duration=course.estimated_duration or 1,
                    start_date=course.start_date,
                    end_date=course.end_date,
                    image_path=course.image.name if course.image else ''
                ).save()
                
                # Relation TEACHES avec l'instructeur
                try:
                    neo_instructor = NeoUser.nodes.get(username=course.instructor.username)
                    neo_instructor.teaches.connect(neo_course)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'   ⚠ Instructor link failed for {course.title}: {e}'
                    ))
                
                count += 1
                if verbose:
                    self.stdout.write(f'   ✓ {course.title}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ {course.title}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ {count}/{courses.count()} courses migrés'))

    def migrate_modules(self, dry_run, verbose, NeoCourse, NeoModule, Module):
        """Migrer les modules"""
        modules = Module.objects.all()
        
        self.stdout.write(f'\n📦 Modules: {modules.count()} à migrer')
        
        if dry_run:
            for module in modules[:5]:
                self.stdout.write(f'   - {module.title}')
            return

        count = 0
        for module in modules:
            try:
                neo_module = NeoModule(
                    title=module.title,
                    description=module.description or '',
                    order=module.order or 0
                ).save()
                
                # Relation CONTAINS avec le cours
                try:
                    neo_course = NeoCourse.nodes.get(title=module.course.title)
                    neo_course.modules.connect(neo_module, {'order': module.order or 0})
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'   ⚠ Course link failed for {module.title}: {e}'
                    ))
                
                count += 1
                if verbose:
                    self.stdout.write(f'   ✓ {module.title}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ {module.title}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ {count}/{modules.count()} modules migrés'))

    def migrate_resources(self, dry_run, verbose, NeoModule, NeoResource, Resource):
        """Migrer les ressources"""
        resources = Resource.objects.all()
        
        self.stdout.write(f'\n📄 Resources: {resources.count()} à migrer')
        
        if dry_run:
            return

        count = 0
        for resource in resources:
            try:
                neo_resource = NeoResource(
                    title=resource.title,
                    resource_type=resource.resource_type or 'fichier',
                    url=resource.url or '',
                    file_path=resource.file.name if resource.file else ''
                ).save()
                
                # Relation HAS_RESOURCE avec le module
                try:
                    neo_module = NeoModule.nodes.get(title=resource.module.title)
                    neo_module.resources.connect(neo_resource, {'order': 0})
                except Exception:
                    pass
                
                count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ {resource.title}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ {count}/{resources.count()} resources migrées'))

    def migrate_evaluations(self, dry_run, verbose, NeoModule, NeoEvaluation, Evaluation):
        """Migrer les évaluations"""
        evaluations = Evaluation.objects.all()
        
        self.stdout.write(f'\n📝 Evaluations: {evaluations.count()} à migrer')
        
        if dry_run:
            return

        count = 0
        for evaluation in evaluations:
            try:
                neo_eval = NeoEvaluation(
                    title=evaluation.title,
                    description=evaluation.description or '',
                    evaluation_type=evaluation.evaluation_type or 'Quiz',
                    deadline=evaluation.deadline,
                    max_score=evaluation.max_score or 100,
                    passing_score=evaluation.passing_score or 60,
                    allow_retake=evaluation.allow_retake or False,
                    max_attempts=evaluation.max_attempts or 1,
                    show_correct_answers=getattr(evaluation, 'show_correct_answers', True),
                    time_limit_minutes=getattr(evaluation, 'time_limit_minutes', None)
                ).save()
                
                # Relation avec le module
                try:
                    neo_module = NeoModule.nodes.get(title=evaluation.module.title)
                    neo_module.evaluations.connect(neo_eval)
                except Exception:
                    pass
                
                count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ {evaluation.title}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ {count}/{evaluations.count()} évaluations migrées'))

    def migrate_questions(self, dry_run, verbose, NeoEvaluation, NeoQuestion, Question):
        """Migrer les questions"""
        questions = Question.objects.all()
        
        self.stdout.write(f'\n❓ Questions: {questions.count()} à migrer')
        
        if dry_run:
            return

        count = 0
        for question in questions:
            try:
                neo_question = NeoQuestion(
                    text=question.text,
                    option1=question.option1,
                    option2=question.option2,
                    option3=question.option3,
                    option4=question.option4,
                    correct_option=question.correct_option,
                    points=question.points or 1.0,
                    order=getattr(question, 'order', 0)
                ).save()
                
                # Relation avec l'évaluation
                try:
                    neo_eval = NeoEvaluation.nodes.get(title=question.evaluation.title)
                    neo_eval.questions.connect(neo_question)
                except Exception:
                    pass
                
                count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ Question: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ {count}/{questions.count()} questions migrées'))

    def migrate_enrollments(self, dry_run, verbose, NeoUser, NeoCourse, Enrollment):
        """Migrer les inscriptions"""
        enrollments = Enrollment.objects.all()
        
        self.stdout.write(f'\n🎓 Enrollments: {enrollments.count()} à migrer')
        
        if dry_run:
            return

        count = 0
        for enrollment in enrollments:
            try:
                neo_student = NeoUser.nodes.get(username=enrollment.student.username)
                neo_course = NeoCourse.nodes.get(title=enrollment.course.title)
                
                neo_student.enrolled_in.connect(neo_course, {
                    'enrolled_on': enrollment.enrolled_on,
                    'certified': enrollment.certified or False,
                    'completion_percent': 0.0
                })
                count += 1
            except Exception as e:
                if verbose:
                    self.stdout.write(self.style.WARNING(f'   ⚠ Enrollment: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ {count}/{enrollments.count()} enrollments migrés'))

    def migrate_submissions(self, dry_run, verbose, NeoUser, NeoEvaluation, Submission):
        """Migrer les soumissions"""
        submissions = Submission.objects.all()
        
        self.stdout.write(f'\n📤 Submissions: {submissions.count()} à migrer')
        
        if dry_run:
            return

        count = 0
        for submission in submissions:
            try:
                neo_student = NeoUser.nodes.get(username=submission.student.username)
                neo_eval = NeoEvaluation.nodes.get(title=submission.evaluation.title)
                
                neo_student.submitted.connect(neo_eval, {
                    'submitted_on': submission.submitted_on,
                    'score': submission.score or 0,
                    'max_score': submission.max_score or 0,
                    'percentage': submission.percentage or 0,
                    'passed': submission.passed or False,
                    'attempt_number': submission.attempt_number or 1,
                    'status': submission.status or 'pending',
                    'instructor_comment': submission.instructor_comment or '',
                    'file_path': submission.file.name if submission.file else ''
                })
                count += 1
            except Exception as e:
                if verbose:
                    self.stdout.write(self.style.WARNING(f'   ⚠ Submission: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ {count}/{submissions.count()} submissions migrées'))

    def migrate_resource_views(self, dry_run, verbose, NeoUser, NeoResource, ResourceView):
        """Migrer les vues de ressources"""
        views = ResourceView.objects.all()
        
        self.stdout.write(f'\n👁️ Resource Views: {views.count()} à migrer')
        
        if dry_run:
            return

        count = 0
        for view in views:
            try:
                neo_student = NeoUser.nodes.get(username=view.student.username)
                neo_resource = NeoResource.nodes.get(title=view.resource.title)
                
                neo_student.viewed.connect(neo_resource, {
                    'viewed_on': view.viewed_on
                })
                count += 1
            except Exception:
                pass

        self.stdout.write(self.style.SUCCESS(f'✅ {count}/{views.count()} vues migrées'))

    def verify_migration(self):
        """Vérifier la migration"""
        self.stdout.write('\n🔍 Vérification...')
        
        # Compter les nœuds
        result, _ = db.cypher_query(
            "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY label"
        )
        
        self.stdout.write('\n📊 Nœuds dans Neo4j:')
        for row in result:
            self.stdout.write(f'   - {row[0]}: {row[1]}')
        
        # Compter les relations
        result, _ = db.cypher_query(
            "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS count ORDER BY rel_type"
        )
        
        self.stdout.write('\n📊 Relations dans Neo4j:')
        for row in result:
            self.stdout.write(f'   - {row[0]}: {row[1]}')
