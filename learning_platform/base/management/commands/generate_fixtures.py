"""
Générateur de données réalistes pour EduSphere LMS
Utilise Faker (fr_FR) pour créer des noms/descriptions français réalistes

Usage:
    python manage.py generate_fixtures --verbose
    python manage.py generate_fixtures --clean --verbose
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
import random
from datetime import timedelta, date
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Génère des données réalistes pour EduSphere LMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Nettoyer la base de données avant génération'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Afficher les détails de chaque création'
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.fake = Faker('fr_FR')
        
        self.stdout.write(self.style.SUCCESS(
            '\n' + '='*60 + '\n'
            'GÉNÉRATION DE FIXTURES RÉALISTES\n'
            'EduSphere LMS\n'
            + '='*60 + '\n'
        ))

        # 1. Nettoyer si demandé
        if options['clean']:
            self.clean_database()

        # 2. Créer les utilisateurs
        self.stdout.write('\n👤 Création des utilisateurs...')
        instructors = self.create_instructors(5)
        students = self.create_students(30)

        # 3. Créer les cours
        self.stdout.write('\n📚 Création des cours...')
        courses = self.create_courses(10, instructors)

        # 4. Inscrire les étudiants
        self.stdout.write('\n🎓 Inscription des étudiants...')
        self.enroll_students(students, courses)

        # 5. Générer les progressions et soumissions
        self.stdout.write('\n📈 Génération des progressions...')
        self.generate_progress(students, courses)

        # 6. Générer les certificats
        self.stdout.write('\n🏆 Génération des certificats...')
        self.generate_certificates(students, courses)

        # 7. Synchroniser vers Neo4j
        self.stdout.write('\n🔄 Synchronisation Neo4j...')
        self.sync_to_neo4j(courses, students, instructors)

        # 8. Afficher le résumé
        self.display_summary()

    def clean_database(self):
        """Nettoie toutes les données existantes (sauf superuser)"""
        self.stdout.write('\n🧹 Nettoyage de la base de données...')
        
        from base.models import (
            Certificate, Submission, Progress, ResourceView, 
            Enrollment, Question, Evaluation, Resource, Module, Course
        )
        
        try:
            Certificate.objects.all().delete()
            self.stdout.write('   ✓ Certificats supprimés')
            
            Submission.objects.all().delete()
            self.stdout.write('   ✓ Soumissions supprimées')
            
            Progress.objects.all().delete()
            self.stdout.write('   ✓ Progressions supprimées')
            
            ResourceView.objects.all().delete()
            self.stdout.write('   ✓ Vues ressources supprimées')
            
            Enrollment.objects.all().delete()
            self.stdout.write('   ✓ Inscriptions supprimées')
            
            Question.objects.all().delete()
            self.stdout.write('   ✓ Questions supprimées')
            
            Evaluation.objects.all().delete()
            self.stdout.write('   ✓ Évaluations supprimées')
            
            Resource.objects.all().delete()
            self.stdout.write('   ✓ Ressources supprimées')
            
            Module.objects.all().delete()
            self.stdout.write('   ✓ Modules supprimés')
            
            Course.objects.all().delete()
            self.stdout.write('   ✓ Cours supprimés')
            
            # Supprimer les users non-superuser
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write('   ✓ Utilisateurs supprimés (sauf admin)')
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠ Erreur nettoyage: {e}'))

    def create_instructors(self, count):
        """Crée des instructeurs avec noms français réalistes"""
        instructors = []
        domains = ['informatique', 'data', 'design', 'business', 'langues']
        
        for i in range(count):
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            username = f"prof_{first_name.lower()}_{last_name.lower()[:3]}"
            email = f"{first_name.lower()}.{last_name.lower()}@univ-paris.fr"
            
            try:
                instructor = User.objects.create_user(
                    username=username[:30],  # Limiter la longueur
                    email=email,
                    password='InstructorPass123!',
                    first_name=first_name,
                    last_name=last_name,
                    role='Instructor'
                )
                instructors.append(instructor)
                
                if self.verbose:
                    self.stdout.write(f'   ✓ {first_name} {last_name} (Instructeur)')
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ Erreur création instructeur: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(instructors)} instructeurs créés'))
        return instructors

    def create_students(self, count):
        """Crée des étudiants avec noms français réalistes"""
        students = []
        
        for i in range(count):
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            username = f"etu_{first_name.lower()}_{last_name.lower()[:3]}_{i}"
            email = f"{first_name.lower()}.{last_name.lower()}@student.edu.fr"
            
            try:
                student = User.objects.create_user(
                    username=username[:30],
                    email=email,
                    password='StudentPass123!',
                    first_name=first_name,
                    last_name=last_name,
                    role='Student'
                )
                students.append(student)
                
                if self.verbose:
                    self.stdout.write(f'   ✓ {first_name} {last_name} (Étudiant)')
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ Erreur création étudiant: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(students)} étudiants créés'))
        return students

    def create_courses(self, count, instructors):
        """Crée des cours réalistes avec modules, ressources et évaluations"""
        from base.models import Course, Module, Resource, Evaluation, Question
        
        courses = []
        
        # Catalogue de cours réalistes par domaine
        course_catalog = [
            # PROGRAMMATION
            {
                'title': 'Python pour Débutants',
                'domain': 'Programmation',
                'level': 'Beginner',
                'duration': 25,
                'description': 'Apprenez les bases de Python, le langage de programmation le plus populaire. Ce cours couvre les variables, les boucles, les fonctions et les structures de données.'
            },
            {
                'title': 'JavaScript Moderne (ES6+)',
                'domain': 'Programmation',
                'level': 'Intermediate',
                'duration': 35,
                'description': 'Maîtrisez JavaScript moderne avec ES6+. Promises, async/await, modules, classes et toutes les fonctionnalités avancées du langage.'
            },
            {
                'title': 'Java pour Applications Enterprise',
                'domain': 'Programmation',
                'level': 'Advanced',
                'duration': 50,
                'description': 'Développez des applications enterprise robustes avec Java. Spring Boot, microservices, patterns de conception et bonnes pratiques.'
            },
            # DATA SCIENCE
            {
                'title': 'Introduction au Machine Learning',
                'domain': 'Data Science',
                'level': 'Intermediate',
                'duration': 40,
                'description': 'Découvrez les algorithmes de machine learning : régression, classification, clustering. Pratique avec Scikit-learn et Python.'
            },
            {
                'title': 'Analyse de Données avec Pandas',
                'domain': 'Data Science',
                'level': 'Beginner',
                'duration': 20,
                'description': 'Manipulez et analysez des données comme un pro avec Pandas et NumPy. Nettoyage, transformation et visualisation de données.'
            },
            # WEB DEVELOPMENT
            {
                'title': 'Développement Web Full-Stack avec Django',
                'domain': 'Web Development',
                'level': 'Intermediate',
                'duration': 45,
                'description': 'Créez des applications web complètes avec Django. Backend, frontend, base de données, authentification et déploiement.'
            },
            {
                'title': 'React.js - De Zéro à Expert',
                'domain': 'Web Development',
                'level': 'Intermediate',
                'duration': 38,
                'description': 'Maîtrisez React.js, la bibliothèque JavaScript la plus utilisée. Hooks, Context, Redux et bonnes pratiques modernes.'
            },
            # DESIGN
            {
                'title': 'Design UI/UX Fondamentaux',
                'domain': 'Design',
                'level': 'Beginner',
                'duration': 30,
                'description': 'Apprenez les principes du design d\'interface et d\'expérience utilisateur. Figma, prototypage et tests utilisateur.'
            },
            # BUSINESS
            {
                'title': 'Gestion de Projet Agile (Scrum)',
                'domain': 'Business',
                'level': 'Beginner',
                'duration': 15,
                'description': 'Devenez un expert de la méthodologie Agile. Scrum, sprints, user stories et outils de gestion de projet.'
            },
            {
                'title': 'Marketing Digital Stratégique',
                'domain': 'Business',
                'level': 'Intermediate',
                'duration': 28,
                'description': 'Stratégies marketing digitales avancées. SEO, SEM, réseaux sociaux, analytics et conversion.'
            },
        ]
        
        # Module templates par domaine
        module_templates = {
            'Programmation': [
                'Introduction et Installation',
                'Les Fondamentaux',
                'Structures de Données',
                'Programmation Orientée Objet',
                'Projet Pratique'
            ],
            'Data Science': [
                'Introduction à la Data Science',
                'Manipulation des Données',
                'Visualisation',
                'Modélisation',
                'Projet Final'
            ],
            'Web Development': [
                'Environnement de Développement',
                'Frontend Basics',
                'Backend et APIs',
                'Base de Données',
                'Déploiement'
            ],
            'Design': [
                'Principes du Design',
                'Outils et Workflow',
                'Design Responsive',
                'Prototypage',
                'Tests Utilisateur'
            ],
            'Business': [
                'Introduction',
                'Méthodologies',
                'Outils et Pratiques',
                'Études de Cas',
                'Certification'
            ]
        }
        
        for i, course_data in enumerate(course_catalog[:count]):
            instructor = random.choice(instructors)
            
            start_date = date.today() - timedelta(days=random.randint(30, 180))
            end_date = start_date + timedelta(days=random.randint(60, 120))
            
            try:
                course = Course.objects.create(
                    title=course_data['title'],
                    description=course_data['description'],
                    instructor=instructor,
                    level=course_data['level'],
                    estimated_duration=course_data['duration'],
                    start_date=start_date,
                    end_date=end_date
                )
                courses.append(course)
                
                if self.verbose:
                    self.stdout.write(f'   ✓ {course.title}')
                
                # Créer les modules
                domain = course_data['domain']
                module_titles = module_templates.get(domain, module_templates['Programmation'])
                
                for order, module_title in enumerate(module_titles[:random.randint(3, 5)], 1):
                    module = Module.objects.create(
                        course=course,
                        title=f"{module_title}",
                        description=self.fake.paragraph(nb_sentences=3),
                        order=order
                    )
                    
                    # Créer ressources (5-10 par module)
                    self.create_resources(module, random.randint(5, 10))
                    
                    # Créer évaluations (2-4 par module)
                    self.create_evaluations(module, random.randint(2, 4))
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ Erreur création cours: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(courses)} cours créés'))
        return courses

    def create_resources(self, module, count):
        """Crée des ressources variées pour un module"""
        from base.models import Resource
        
        resource_types = ['video', 'pdf', 'article', 'file']
        type_weights = [0.4, 0.3, 0.2, 0.1]  # 40% vidéos, 30% PDFs, etc.
        
        for i in range(count):
            res_type = random.choices(resource_types, weights=type_weights)[0]
            
            # URLs réalistes selon le type
            if res_type == 'video':
                url = f"https://www.youtube.com/watch?v={self.fake.bothify('???????????')}"
                title = f"Vidéo: {self.fake.sentence(nb_words=4)}"
            elif res_type == 'pdf':
                url = f"https://drive.google.com/file/d/{self.fake.bothify('?????????????????')}/view"
                title = f"PDF: {self.fake.sentence(nb_words=4)}"
            elif res_type == 'article':
                url = f"https://medium.com/@{self.fake.user_name()}/{self.fake.slug()}"
                title = f"Article: {self.fake.sentence(nb_words=5)}"
            else:
                url = f"https://dropbox.com/s/{self.fake.bothify('?????????')}/{self.fake.file_name()}"
                title = f"Fichier: {self.fake.sentence(nb_words=3)}"
            
            try:
                Resource.objects.create(
                    module=module,
                    title=title[:100],
                    resource_type=res_type,
                    url=url
                )
            except Exception:
                pass

    def create_evaluations(self, module, count):
        """Crée des évaluations avec questions réalistes"""
        from base.models import Evaluation, Question
        
        eval_types = ['Quiz', 'Assignment']
        
        for i in range(count):
            eval_type = random.choice(eval_types)
            deadline = timezone.now() + timedelta(days=random.randint(7, 30))
            
            try:
                evaluation = Evaluation.objects.create(
                    module=module,
                    title=f"{'Quiz' if eval_type == 'Quiz' else 'Devoir'}: {module.title}",
                    description=self.fake.paragraph(nb_sentences=2),
                    evaluation_type=eval_type,
                    max_score=100,
                    deadline=deadline
                )
                
                # Créer des questions pour les Quiz
                if eval_type == 'Quiz':
                    self.create_questions(evaluation, random.randint(5, 10))
                    
            except Exception:
                pass

    def create_questions(self, evaluation, count):
        """Crée des questions à choix multiples réalistes"""
        from base.models import Question
        
        question_templates = [
            ("Quelle est la bonne définition de {concept} ?", "concept"),
            ("Quel est le résultat de {operation} ?", "operation"),
            ("Parmi les suivants, lequel est {property} ?", "property"),
            ("Comment appelle-t-on {phenomenon} ?", "phenomenon"),
            ("Quelle méthode permet de {action} ?", "action"),
        ]
        
        for i in range(count):
            template = random.choice(question_templates)
            concept = self.fake.word()
            question_text = template[0].replace('{' + template[1] + '}', concept)
            
            # Options réalistes
            correct = self.fake.sentence(nb_words=3)
            distractors = [self.fake.sentence(nb_words=3) for _ in range(3)]
            
            # Mélanger les options
            options = [correct] + distractors
            random.shuffle(options)
            correct_index = options.index(correct)
            
            try:
                Question.objects.create(
                    evaluation=evaluation,
                    text=f"{i+1}. {question_text}",
                    option_a=options[0][:200],
                    option_b=options[1][:200],
                    option_c=options[2][:200],
                    option_d=options[3][:200],
                    correct_answer=['A', 'B', 'C', 'D'][correct_index],
                    points=random.randint(1, 10)
                )
            except Exception:
                pass

    def enroll_students(self, students, courses):
        """Inscrit les étudiants aux cours de manière réaliste"""
        from base.models import Enrollment
        
        enrollments_created = 0
        
        for student in students:
            # 70% inscrits à 1-3 cours, 30% à 4-6 cours
            if random.random() < 0.7:
                num_courses = random.randint(1, 3)
            else:
                num_courses = random.randint(4, min(6, len(courses)))
            
            selected_courses = random.sample(courses, min(num_courses, len(courses)))
            
            for course in selected_courses:
                try:
                    # enrolled_on is auto_now_add, don't set it manually
                    Enrollment.objects.create(
                        student=student,
                        course=course
                    )
                    enrollments_created += 1
                except Exception:
                    pass
        
        self.stdout.write(self.style.SUCCESS(f'✅ {enrollments_created} inscriptions créées'))

    def generate_progress(self, students, courses):
        """Génère des progressions et soumissions réalistes"""
        from base.models import Enrollment, Progress, Submission, ResourceView
        
        submissions_created = 0
        progress_created = 0
        
        for student in students:
            enrollments = Enrollment.objects.filter(student=student)
            
            for enrollment in enrollments:
                course = enrollment.course
                modules = course.modules.all()
                
                # Progression : 0%, 25%, 50%, 75%, 100%
                completion_levels = [0, 25, 50, 75, 100]
                completion = random.choice(completion_levels)
                
                modules_to_complete = int(len(modules) * completion / 100)
                
                for i, module in enumerate(modules[:modules_to_complete]):
                    # Créer progress
                    try:
                        Progress.objects.update_or_create(
                            enrollment=enrollment,
                            module=module,
                            defaults={
                                'completion_percent': 100,
                                'is_completed': True,
                                'resources_viewed': module.resources.count(),
                                'total_resources': module.resources.count()
                            }
                        )
                        progress_created += 1
                    except Exception:
                        pass
                    
                    # ResourceViews
                    for resource in module.resources.all()[:random.randint(1, 5)]:
                        try:
                            ResourceView.objects.get_or_create(
                                student=student,
                                resource=resource
                            )
                        except Exception:
                            pass
                    
                    # Soumissions aux évaluations
                    for evaluation in module.evaluations.all():
                        if random.random() < 0.6:  # 60% de chance de soumettre
                            try:
                                score = random.randint(40, 100)
                                Submission.objects.create(
                                    student=student,
                                    evaluation=evaluation,
                                    submitted_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                                    score=score,
                                    is_graded=True
                                )
                                submissions_created += 1
                            except Exception:
                                pass
        
        self.stdout.write(self.style.SUCCESS(f'✅ {progress_created} progressions, {submissions_created} soumissions'))

    def generate_certificates(self, students, courses):
        """Génère des certificats pour les cours complétés"""
        from base.models import Enrollment, Progress, Certificate
        import uuid
        
        certificates_created = 0
        
        for student in students:
            enrollments = Enrollment.objects.filter(student=student)
            
            for enrollment in enrollments:
                course = enrollment.course
                modules = course.modules.all()
                
                if not modules.exists():
                    continue
                
                # Vérifier si 100% des modules sont complétés
                completed_modules = Progress.objects.filter(
                    enrollment=enrollment,
                    is_completed=True
                ).count()
                
                if completed_modules >= modules.count():
                    # Créer le certificat
                    try:
                        cert_number = f"CERT-{uuid.uuid4().hex[:8].upper()}"
                        Certificate.objects.create(
                            student=student,
                            course=course,
                            certificate_number=cert_number,
                            issued_on=date.today() - timedelta(days=random.randint(1, 30))
                        )
                        certificates_created += 1
                        
                        if self.verbose:
                            self.stdout.write(f'   ✓ Certificat {cert_number} pour {student.username}')
                            
                    except Exception as e:
                        if self.verbose:
                            self.stdout.write(self.style.WARNING(f'   ⚠ Erreur: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ {certificates_created} certificats générés'))

    def sync_to_neo4j(self, courses, students, instructors):
        """Synchronise les données vers Neo4j"""
        try:
            from base.neo_models import NeoUser, NeoCourse, sync_django_user_to_neo4j
            from base.models import Enrollment
            from datetime import date
            from neomodel import db
            from django.conf import settings
            
            # Initialiser connexion
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
            
            synced_users = 0
            synced_courses = 0
            synced_enrollments = 0
            
            # Sync instructors
            for instructor in instructors:
                try:
                    sync_django_user_to_neo4j(instructor)
                    synced_users += 1
                except Exception:
                    pass
            
            # Sync students
            for student in students:
                try:
                    sync_django_user_to_neo4j(student)
                    synced_users += 1
                except Exception:
                    pass
            
            self.stdout.write(f'   ✓ {synced_users} utilisateurs synchronisés')
            
            # Sync courses
            for course in courses:
                try:
                    neo_course = NeoCourse.nodes.get_or_none(title=course.title)
                    if not neo_course:
                        neo_course = NeoCourse(
                            title=course.title,
                            description=course.description or '',
                            level=course.level or 'Beginner',
                            estimated_duration=course.estimated_duration or 1,
                            start_date=course.start_date,
                            end_date=course.end_date
                        ).save()
                        
                        # Lier à l'instructeur
                        neo_instructor = NeoUser.nodes.get_or_none(username=course.instructor.username)
                        if neo_instructor:
                            neo_instructor.teaches.connect(neo_course)
                        
                        synced_courses += 1
                except Exception:
                    pass
            
            self.stdout.write(f'   ✓ {synced_courses} cours synchronisés')
            
            # Sync enrollments
            enrollments = Enrollment.objects.all()
            for enrollment in enrollments:
                try:
                    neo_user = NeoUser.nodes.get_or_none(username=enrollment.student.username)
                    neo_course = NeoCourse.nodes.get_or_none(title=enrollment.course.title)
                    
                    if neo_user and neo_course:
                        if neo_course not in neo_user.enrolled_in.all():
                            neo_user.enrolled_in.connect(neo_course, {
                                'enrolled_on': enrollment.enrolled_on,
                                'completion_percent': 0.0,
                                'certified': False
                            })
                            synced_enrollments += 1
                except Exception:
                    pass
            
            self.stdout.write(f'   ✓ {synced_enrollments} inscriptions synchronisées')
            self.stdout.write(self.style.SUCCESS('✅ Synchronisation Neo4j terminée'))
            
        except ImportError:
            self.stdout.write(self.style.WARNING('   ⚠ Neomodel non disponible - sync ignorée'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠ Erreur sync Neo4j: {e}'))

    def display_summary(self):
        """Affiche un résumé des données créées"""
        from base.models import Course, Module, Resource, Evaluation, Question, Enrollment, Submission, Certificate
        
        self.stdout.write(self.style.SUCCESS(
            '\n' + '='*60 + '\n'
            'RÉSUMÉ DES DONNÉES CRÉÉES\n'
            + '='*60
        ))
        
        self.stdout.write(f'''
📊 Statistiques:
   • Instructeurs: {User.objects.filter(role='Instructor').count()}
   • Étudiants: {User.objects.filter(role='Student').count()}
   • Cours: {Course.objects.count()}
   • Modules: {Module.objects.count()}
   • Ressources: {Resource.objects.count()}
   • Évaluations: {Evaluation.objects.count()}
   • Questions: {Question.objects.count()}
   • Inscriptions: {Enrollment.objects.count()}
   • Soumissions: {Submission.objects.count()}
   • Certificats: {Certificate.objects.count()}

✨ Génération terminée avec succès!

🔐 Credentials:
   • Instructeurs: mot de passe = InstructorPass123!
   • Étudiants: mot de passe = StudentPass123!
''')
