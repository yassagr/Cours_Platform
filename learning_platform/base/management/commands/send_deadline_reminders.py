"""
Management command pour envoyer des rappels de deadline
À exécuter via cron job: python manage.py send_deadline_reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from base.models import Evaluation, Submission, Notification, User, Enrollment


class Command(BaseCommand):
    help = 'Envoie des rappels de deadline pour les évaluations à venir (3 jours avant)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Nombre de jours avant la deadline pour envoyer le rappel (défaut: 3)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher les notifications qui seraient envoyées sans les créer'
        )

    def handle(self, *args, **options):
        days_before = options['days']
        dry_run = options['dry_run']
        
        # Date cible (deadline dans X jours)
        target_date = timezone.now().date() + timedelta(days=days_before)
        
        self.stdout.write(f"Recherche des évaluations avec deadline le {target_date}...")
        
        # Trouver les évaluations avec deadline à cette date
        evaluations = Evaluation.objects.filter(deadline=target_date)
        
        sent_count = 0
        skipped_count = 0
        
        for evaluation in evaluations:
            course = evaluation.module.course
            self.stdout.write(f"  Traitement: {evaluation.title} ({course.title})")
            
            # Trouver les étudiants inscrits au cours
            enrolled_students = User.objects.filter(
                enrollments__course=course,
                role='Student'
            )
            
            for student in enrolled_students:
                # Vérifier si l'étudiant a déjà soumis
                already_submitted = Submission.objects.filter(
                    evaluation=evaluation,
                    student=student
                ).exists()
                
                if already_submitted:
                    skipped_count += 1
                    continue
                
                # Vérifier si notification déjà envoyée aujourd'hui
                already_notified = Notification.objects.filter(
                    recipient=student,
                    related_evaluation=evaluation,
                    notification_type='deadline_reminder',
                    sent_on__date=timezone.now().date()
                ).exists()
                
                if already_notified:
                    skipped_count += 1
                    continue
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"    [DRY-RUN] Notification pour {student.username}"
                        )
                    )
                    sent_count += 1
                else:
                    # Créer la notification
                    Notification.objects.create(
                        recipient=student,
                        title=f"⏰ Rappel: Deadline dans {days_before} jours",
                        message=f"L'évaluation '{evaluation.title}' doit être rendue avant le {evaluation.deadline}.",
                        notification_type='deadline_reminder',
                        priority='high',
                        related_course=course,
                        related_evaluation=evaluation,
                        action_url=f"/modules/course/{course.id}/?module_id={evaluation.module.id}"
                    )
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    ✓ Notification envoyée à {student.username}"
                        )
                    )
        
        # Résumé
        self.stdout.write("")
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY-RUN] {sent_count} notifications auraient été envoyées."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ {sent_count} rappels de deadline envoyés."
                )
            )
        
        self.stdout.write(f"ℹ️  {skipped_count} étudiants ignorés (déjà soumis ou déjà notifiés)")
