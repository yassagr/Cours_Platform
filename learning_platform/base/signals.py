# signals.py - Signaux Django pour EduSphere LMS
# Ce fichier contient les signaux qui automatisent certaines actions

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from .models import ResourceView, Submission, Progress, Enrollment

logger = logging.getLogger('base')


@receiver(post_save, sender=ResourceView)
def update_progress_on_resource_view(sender, instance, created, **kwargs):
    """
    Met à jour automatiquement la progression d'un module 
    lorsqu'un étudiant visualise une ressource.
    """
    if created:
        student = instance.student
        module = instance.resource.module
        course = module.course
        
        # Trouver l'inscription de l'étudiant
        enrollment = Enrollment.objects.filter(student=student, course=course).first()
        if not enrollment:
            return
        
        # Compter les ressources vues dans ce module
        total_resources = module.resources.count()
        if total_resources == 0:
            return
            
        viewed_resources = ResourceView.objects.filter(
            student=student,
            resource__module=module
        ).values('resource').distinct().count()
        
        progress_percentage = (viewed_resources / total_resources) * 100
        
        # Mettre à jour ou créer le Progress
        progress, _ = Progress.objects.update_or_create(
            enrollment=enrollment,
            module=module,
            defaults={
                'completion_percent': min(progress_percentage, 100),
                'resources_viewed': viewed_resources,
                'total_resources': total_resources,
                'is_completed': progress_percentage >= 100
            }
        )
        
        logger.info(
            f"Progress updated for {student.username} in module '{module.title}': "
            f"{progress_percentage:.1f}%"
        )


@receiver(post_save, sender=Submission)
def update_progress_on_submission(sender, instance, created, **kwargs):
    """
    Met à jour la progression lorsqu'un étudiant soumet une évaluation.
    Un quiz réussi contribue à la progression du module.
    """
    if instance.status == 'graded' and instance.passed:
        student = instance.student
        evaluation = instance.evaluation
        module = evaluation.module
        course = module.course
        
        # Trouver l'inscription de l'étudiant
        enrollment = Enrollment.objects.filter(student=student, course=course).first()
        if not enrollment:
            return
        
        # Vérifier s'il y a d'autres évaluations obligatoires dans ce module
        total_evals = module.evaluations.count()
        passed_evals = Submission.objects.filter(
            student=student,
            evaluation__module=module,
            passed=True
        ).values('evaluation').distinct().count()
        
        # Si toutes les évaluations sont passées, marquer le module comme complété
        if passed_evals >= total_evals:
            progress, _ = Progress.objects.update_or_create(
                enrollment=enrollment,
                module=module,
                defaults={
                    'completion_percent': 100,
                    'evaluations_completed': passed_evals,
                    'total_evaluations': total_evals,
                    'is_completed': True
                }
            )
            
            logger.info(
                f"Module '{module.title}' completed by {student.username} "
                f"after passing all evaluations"
            )


# =====================================================
# NEO4J SYNCHRONIZATION SIGNALS
# =====================================================

from django.contrib.auth import get_user_model


@receiver(post_save, sender=get_user_model())
def sync_user_to_neo4j(sender, instance, created, **kwargs):
    """
    Signal déclenché après chaque save() d'un User Django.
    Crée ou met à jour le NeoUser correspondant dans Neo4j.
    
    Ceci garantit que les nouveaux utilisateurs inscrits via le site
    sont automatiquement synchronisés dans le graphe Neo4j.
    """
    try:
        from base.neo_models import NeoUser
        from neomodel import db
        from django.conf import settings
        
        # Assurer la connexion Neo4j
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        try:
            # Essayer de récupérer le NeoUser existant
            neo_user = NeoUser.nodes.get(username=instance.username)
            
            # Mise à jour des champs
            neo_user.email = instance.email
            neo_user.first_name = instance.first_name
            neo_user.last_name = instance.last_name
            neo_user.is_active = instance.is_active
            neo_user.is_staff = instance.is_staff
            
            if hasattr(instance, 'role'):
                neo_user.role = instance.role
            
            neo_user.save()
            logger.debug(f"NeoUser mis à jour: {instance.username}")
            
        except NeoUser.DoesNotExist:
            # Création d'un nouveau NeoUser
            neo_user = NeoUser(
                username=instance.username,
                email=instance.email,
                first_name=instance.first_name,
                last_name=instance.last_name,
                is_active=instance.is_active,
                is_staff=instance.is_staff,
                role=getattr(instance, 'role', 'Student'),
                date_joined=instance.date_joined
            ).save()
            logger.info(f"NeoUser créé: {instance.username}")
            
    except ImportError:
        # Neomodel pas encore importé (au démarrage)
        pass
    except Exception as e:
        # Ne pas faire échouer l'opération Django si Neo4j est down
        logger.warning(f"Sync Neo4j échouée pour {instance.username}: {e}")


# =====================================================
# SYNC COURSE TO NEO4J
# =====================================================

from .models import Course


@receiver(post_save, sender=Course)
def sync_course_to_neo4j(sender, instance, created, **kwargs):
    """
    Signal déclenché après chaque save() d'un Course Django.
    Crée ou met à jour le NeoCourse correspondant dans Neo4j.
    """
    try:
        from base.neo_models import NeoCourse, NeoUser
        from neomodel import db
        from django.conf import settings
        
        # Assurer la connexion Neo4j
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        if created:
            # Création d'un nouveau NeoCourse
            neo_course = NeoCourse(
                title=instance.title,
                description=instance.description or '',
                level=instance.level or 'Beginner',
                estimated_duration=instance.estimated_duration or 1,
                start_date=instance.start_date,
                end_date=instance.end_date,
                image_path=instance.image.name if instance.image else ''
            ).save()
            
            # Créer relation TEACHES avec l'instructeur
            if instance.instructor:
                try:
                    neo_instructor = NeoUser.nodes.get(username=instance.instructor.username)
                    neo_instructor.teaches.connect(neo_course)
                except NeoUser.DoesNotExist:
                    pass
            
            logger.info(f"NeoCourse créé: {instance.title}")
        else:
            # Mise à jour
            try:
                neo_course = NeoCourse.nodes.get(title=instance.title)
                neo_course.description = instance.description or ''
                neo_course.level = instance.level or 'Beginner'
                neo_course.estimated_duration = instance.estimated_duration or 1
                neo_course.start_date = instance.start_date
                neo_course.end_date = instance.end_date
                neo_course.save()
                logger.debug(f"NeoCourse mis à jour: {instance.title}")
            except NeoCourse.DoesNotExist:
                # Créer si n'existe pas
                neo_course = NeoCourse(
                    title=instance.title,
                    description=instance.description or '',
                    level=instance.level or 'Beginner',
                    estimated_duration=instance.estimated_duration or 1,
                    start_date=instance.start_date,
                    end_date=instance.end_date,
                    image_path=instance.image.name if instance.image else ''
                ).save()
                logger.info(f"NeoCourse créé (sync): {instance.title}")
                
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Sync Neo4j échouée pour course {instance.title}: {e}")


# =====================================================
# SYNC ENROLLMENT TO NEO4J
# =====================================================

from django.db.models.signals import post_delete


@receiver(post_save, sender=Enrollment)
def sync_enrollment_to_neo4j(sender, instance, created, **kwargs):
    """
    Signal déclenché après chaque save() d'un Enrollment Django.
    Crée la relation ENROLLED_IN dans Neo4j.
    """
    if created:
        try:
            from base.neo_models import NeoUser, NeoCourse
            from neomodel import db
            from django.conf import settings
            
            # Assurer la connexion
            if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
                db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
            
            # Récupérer les nœuds
            neo_user = NeoUser.nodes.get_or_none(username=instance.student.username)
            neo_course = NeoCourse.nodes.get_or_none(title=instance.course.title)
            
            if neo_user and neo_course:
                # Vérifier si relation existe déjà
                if neo_course not in neo_user.enrolled_in.all():
                    neo_user.enrolled_in.connect(neo_course, {
                        'enrolled_on': instance.enrolled_on,
                        'completion_percent': 0.0,
                        'certified': instance.certified
                    })
                    logger.info(f"ENROLLED_IN créé: {instance.student.username} -> {instance.course.title}")
                    
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Sync Neo4j échouée pour enrollment: {e}")


@receiver(post_delete, sender=Enrollment)
def delete_enrollment_from_neo4j(sender, instance, **kwargs):
    """
    Signal déclenché après suppression d'un Enrollment Django.
    Supprime la relation ENROLLED_IN dans Neo4j.
    """
    try:
        from base.neo_models import NeoUser, NeoCourse
        from neomodel import db
        from django.conf import settings
        
        # Assurer la connexion
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        neo_user = NeoUser.nodes.get_or_none(username=instance.student.username)
        neo_course = NeoCourse.nodes.get_or_none(title=instance.course.title)
        
        if neo_user and neo_course:
            neo_user.enrolled_in.disconnect(neo_course)
            logger.info(f"ENROLLED_IN supprimé: {instance.student.username} -> {instance.course.title}")
            
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Sync Neo4j delete échouée pour enrollment: {e}")


# =====================================================
# SYNC MODULE TO NEO4J
# =====================================================

from .models import Module


@receiver(post_save, sender=Module)
def sync_module_to_neo4j(sender, instance, created, **kwargs):
    """Synchronise les modules vers Neo4j"""
    try:
        from base.neo_models import NeoModule, NeoCourse
        from neomodel import db
        from django.conf import settings
        
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        # Trouver ou créer le module
        neo_module = NeoModule.nodes.get_or_none(title=instance.title)
        
        if created or not neo_module:
            neo_module = NeoModule(
                title=instance.title,
                description=instance.description or '',
                order=instance.order or 0
            ).save()
            
            # Lier au cours
            neo_course = NeoCourse.nodes.get_or_none(title=instance.course.title)
            if neo_course and neo_module not in neo_course.modules.all():
                neo_course.modules.connect(neo_module)
            
            logger.info(f"NeoModule créé: {instance.title}")
        else:
            neo_module.description = instance.description or ''
            neo_module.order = instance.order or 0
            neo_module.save()
            
    except Exception as e:
        logger.warning(f"Sync Neo4j échouée pour module {instance.title}: {e}")


# =====================================================
# SYNC RESOURCE TO NEO4J
# =====================================================

from .models import Resource


@receiver(post_save, sender=Resource)
def sync_resource_to_neo4j(sender, instance, created, **kwargs):
    """Synchronise les ressources vers Neo4j"""
    try:
        from base.neo_models import NeoResource, NeoModule
        from neomodel import db
        from django.conf import settings
        
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        if created:
            neo_resource = NeoResource(
                title=instance.title,
                resource_type=instance.resource_type or 'file',
                url=instance.url or ''
            ).save()
            
            # Lier au module
            neo_module = NeoModule.nodes.get_or_none(title=instance.module.title)
            if neo_module:
                neo_module.resources.connect(neo_resource)
            
            logger.info(f"NeoResource créé: {instance.title}")
            
    except Exception as e:
        logger.warning(f"Sync Neo4j échouée pour resource {instance.title}: {e}")


# =====================================================
# SYNC EVALUATION TO NEO4J
# =====================================================

from .models import Evaluation


@receiver(post_save, sender=Evaluation)
def sync_evaluation_to_neo4j(sender, instance, created, **kwargs):
    """Synchronise les évaluations vers Neo4j"""
    try:
        from base.neo_models import NeoEvaluation, NeoModule
        from neomodel import db
        from django.conf import settings
        
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        if created:
            neo_eval = NeoEvaluation(
                title=instance.title,
                description=instance.description or '',
                evaluation_type=instance.evaluation_type or 'Quiz',
                max_score=instance.max_score or 100,
                deadline=instance.deadline
            ).save()
            
            # Lier au module
            neo_module = NeoModule.nodes.get_or_none(title=instance.module.title)
            if neo_module:
                neo_module.evaluations.connect(neo_eval)
            
            logger.info(f"NeoEvaluation créé: {instance.title}")
            
    except Exception as e:
        logger.warning(f"Sync Neo4j échouée pour evaluation {instance.title}: {e}")


# =====================================================
# SYNC QUESTION TO NEO4J
# =====================================================

from .models import Question


@receiver(post_save, sender=Question)
def sync_question_to_neo4j(sender, instance, created, **kwargs):
    """Synchronise les questions vers Neo4j"""
    try:
        from base.neo_models import NeoQuestion, NeoEvaluation
        from neomodel import db
        from django.conf import settings
        
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        if created:
            neo_question = NeoQuestion(
                text=instance.text,
                option1=instance.option1 or '',
                option2=instance.option2 or '',
                option3=instance.option3 or '',
                option4=instance.option4 or '',
                correct_option=instance.correct_option or 'A',
                points=instance.points or 1
            ).save()
            
            # Lier à l'évaluation
            neo_eval = NeoEvaluation.nodes.get_or_none(title=instance.evaluation.title)
            if neo_eval:
                neo_eval.questions.connect(neo_question)
            
            logger.info(f"NeoQuestion créé: {instance.text[:30]}...")
            
    except Exception as e:
        logger.warning(f"Sync Neo4j échouée pour question: {e}")


# =====================================================
# DELETE SIGNALS - Suppression dans Neo4j
# =====================================================

@receiver(post_delete, sender=Module)
def delete_module_from_neo4j(sender, instance, **kwargs):
    """Supprime le module de Neo4j"""
    try:
        from base.neo_models import NeoModule
        from neomodel import db
        from django.conf import settings
        
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        neo_module = NeoModule.nodes.get_or_none(title=instance.title)
        if neo_module:
            neo_module.delete()
            logger.info(f"NeoModule supprimé: {instance.title}")
    except Exception as e:
        logger.warning(f"Delete Neo4j échouée pour module: {e}")


@receiver(post_delete, sender=Resource)
def delete_resource_from_neo4j(sender, instance, **kwargs):
    """Supprime la ressource de Neo4j"""
    try:
        from base.neo_models import NeoResource
        from neomodel import db
        from django.conf import settings
        
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        neo_resource = NeoResource.nodes.get_or_none(title=instance.title)
        if neo_resource:
            neo_resource.delete()
            logger.info(f"NeoResource supprimé: {instance.title}")
    except Exception as e:
        logger.warning(f"Delete Neo4j échouée pour resource: {e}")


@receiver(post_delete, sender=Evaluation)
def delete_evaluation_from_neo4j(sender, instance, **kwargs):
    """Supprime l'évaluation de Neo4j"""
    try:
        from base.neo_models import NeoEvaluation
        from neomodel import db
        from django.conf import settings
        
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        neo_eval = NeoEvaluation.nodes.get_or_none(title=instance.title)
        if neo_eval:
            neo_eval.delete()
            logger.info(f"NeoEvaluation supprimé: {instance.title}")
    except Exception as e:
        logger.warning(f"Delete Neo4j échouée pour evaluation: {e}")


@receiver(post_delete, sender=Question)
def delete_question_from_neo4j(sender, instance, **kwargs):
    """Supprime la question de Neo4j"""
    try:
        from base.neo_models import NeoQuestion
        from neomodel import db
        from django.conf import settings
        
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        neo_question = NeoQuestion.nodes.get_or_none(text=instance.text)
        if neo_question:
            neo_question.delete()
            logger.info(f"NeoQuestion supprimé: {instance.text[:30]}...")
    except Exception as e:
        logger.warning(f"Delete Neo4j échouée pour question: {e}")


@receiver(post_delete, sender=Course)
def delete_course_from_neo4j(sender, instance, **kwargs):
    """Supprime le cours de Neo4j"""
    try:
        from base.neo_models import NeoCourse
        from neomodel import db
        from django.conf import settings
        
        if hasattr(settings, 'NEOMODEL_NEO4J_BOLT_URL'):
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
        
        neo_course = NeoCourse.nodes.get_or_none(title=instance.title)
        if neo_course:
            neo_course.delete()
            logger.info(f"NeoCourse supprimé: {instance.title}")
    except Exception as e:
        logger.warning(f"Delete Neo4j échouée pour course: {e}")
