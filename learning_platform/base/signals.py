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

