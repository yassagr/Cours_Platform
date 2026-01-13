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
