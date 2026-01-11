from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# =====================
# Utilisateur Personnalisé (User)
# =====================

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Student', 'Student'),
        ('Instructor', 'Instructor'),
        ('Admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Student')

    def __str__(self):
        return f"{self.username}({self.role})"


# =====================
# Cours (Course)
# =====================

LEVEL_CHOICES = [
    ('Beginner', 'Beginner'),
    ('Intermediate', 'Intermediate'),
    ('Advanced', 'Advanced'),
]

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    estimated_duration = models.IntegerField(help_text="Durée estimée en heures")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=['instructor']),
        ]


# =====================
# Module
# =====================

class Module(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    order = models.PositiveIntegerField(default=0)  # Pour ordonner les modules

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    class Meta:
        ordering = ['order']


# =====================
# Ressource (Resource)
# =====================

RESOURCE_TYPE_CHOICES = [
    ('video', 'Video'),
    ('pdf', 'PDF'),
    ('image', 'Image'),
    ('fichier', 'Fichier'),
]

class Resource(models.Model):
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPE_CHOICES)
    file = models.FileField(upload_to='resources/')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="resources")

    def __str__(self):
        return self.title


# =====================
# Suivi de Consultation de Ressource (ResourceView)
# =====================

class ResourceView(models.Model):
    """Enregistre quand un étudiant consulte une ressource"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_views')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='views')
    viewed_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'resource']
        indexes = [
            models.Index(fields=['student', 'resource']),
        ]

    def __str__(self):
        return f"{self.student.username} viewed {self.resource.title}"


# =====================
# Inscription (Enrollment)
# =====================

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_on = models.DateField(auto_now_add=True)
    certified = models.BooleanField(default=False)

    class Meta:
        unique_together = ['student', 'course']
        indexes = [
            models.Index(fields=['student', 'course']),
        ]

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"


# =====================
# Progression par Module (Progress)
# =====================

class Progress(models.Model):
    """Progression d'un étudiant pour un module spécifique"""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="progresses")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="progresses")
    completion_percent = models.FloatField(default=0)
    resources_viewed = models.IntegerField(default=0)
    total_resources = models.IntegerField(default=0)
    evaluations_completed = models.IntegerField(default=0)
    total_evaluations = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_on = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['enrollment', 'module']
        verbose_name_plural = "Progresses"

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.module.title} ({self.completion_percent}%)"


# =====================
# Progression par Cours (CourseProgress)
# =====================

class CourseProgress(models.Model):
    """Progression globale d'un étudiant pour un cours entier"""
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='course_progress')
    overall_completion_percent = models.FloatField(default=0)
    modules_completed = models.IntegerField(default=0)
    total_modules = models.IntegerField(default=0)
    average_score = models.FloatField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.enrollment.course.title} ({self.overall_completion_percent}%)"


# =====================
# Évaluation (Evaluation)
# =====================

EVALUATION_TYPE_CHOICES = [
    ('Quiz', 'Quiz'),
    ('Assignment', 'Assignment'),
]

class Evaluation(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)  # Description de l'évaluation
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='evaluations')
    evaluation_type = models.CharField(max_length=10, choices=EVALUATION_TYPE_CHOICES)
    deadline = models.DateField()
    
    # Nouveaux champs pour la gestion des quiz
    max_score = models.IntegerField(default=100, help_text="Score maximum pour cette évaluation")
    passing_score = models.IntegerField(default=60, help_text="Score minimum pour réussir (%)")
    allow_retake = models.BooleanField(default=False, help_text="Permettre plusieurs tentatives")
    max_attempts = models.IntegerField(default=1, help_text="Nombre maximum de tentatives (si retake autorisé)")
    show_correct_answers = models.BooleanField(default=True, help_text="Montrer les corrections après soumission")
    time_limit_minutes = models.IntegerField(null=True, blank=True, help_text="Limite de temps en minutes (optionnel)")

    def __str__(self):
        return self.title

    def get_total_questions(self):
        """Retourne le nombre total de questions pour cette évaluation"""
        return self.questions.count()


# =====================
# Question
# =====================

OPTION_CHOICES = [
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
]

class Question(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name="Énoncé de la question")
    option1 = models.CharField(max_length=500, verbose_name="Option A")
    option2 = models.CharField(max_length=500, verbose_name="Option B")
    option3 = models.CharField(max_length=500, verbose_name="Option C")
    option4 = models.CharField(max_length=500, verbose_name="Option D")
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES, verbose_name="Bonne réponse")
    points = models.FloatField(default=1, help_text="Points pour cette question")
    order = models.PositiveIntegerField(default=0)  # Pour ordonner les questions

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text[:50] + "..." if len(self.text) > 50 else self.text

    def get_option_text(self, option_letter):
        """Retourne le texte d'une option par sa lettre"""
        options = {
            'A': self.option1,
            'B': self.option2,
            'C': self.option3,
            'D': self.option4,
        }
        return options.get(option_letter, '')


# =====================
# Soumission (Submission)
# =====================

SUBMISSION_STATUS_CHOICES = [
    ('pending', 'En attente de correction'),
    ('graded', 'Noté'),
    ('late', 'Soumis en retard'),
]

class Submission(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    submitted_on = models.DateTimeField(auto_now_add=True)
    
    # Champs pour les devoirs (Assignments)
    file = models.FileField(upload_to='submissions/', blank=True, null=True)
    
    # Champs pour le scoring
    score = models.FloatField(null=True, blank=True, help_text="Score obtenu")
    max_score = models.FloatField(null=True, blank=True, help_text="Score maximum possible")
    percentage = models.FloatField(null=True, blank=True, help_text="Pourcentage de réussite")
    passed = models.BooleanField(default=False, help_text="A réussi l'évaluation")
    
    # Champs pour la correction
    graded_on = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='graded_submissions')
    instructor_comment = models.TextField(blank=True, verbose_name="Commentaire de l'instructeur")
    status = models.CharField(max_length=20, choices=SUBMISSION_STATUS_CHOICES, default='pending')
    
    # Gestion des tentatives multiples
    attempt_number = models.IntegerField(default=1)

    class Meta:
        unique_together = ['evaluation', 'student', 'attempt_number']
        ordering = ['-submitted_on']
        indexes = [
            models.Index(fields=['evaluation', 'student']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.evaluation.title} (Attempt {self.attempt_number})"

    def calculate_score(self):
        """Calcule le score automatiquement pour les quiz"""
        if self.evaluation.evaluation_type != 'Quiz':
            return
        
        total_points = 0
        earned_points = 0
        
        for answer in self.submitted_answers.all():
            total_points += answer.question.points
            if answer.is_correct:
                earned_points += answer.question.points
        
        self.score = earned_points
        self.max_score = total_points
        self.percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        self.passed = self.percentage >= self.evaluation.passing_score
        self.status = 'graded'


# =====================
# Réponse Soumise (SubmittedAnswer)
# =====================

class SubmittedAnswer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='submitted_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    selected_option = models.CharField(max_length=1, choices=OPTION_CHOICES, blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.FloatField(default=0)

    class Meta:
        unique_together = ['submission', 'question']

    def __str__(self):
        return f"Answer for Q{self.question.id} by {self.submission.student.username}"

    def save(self, *args, **kwargs):
        """Calcule automatiquement si la réponse est correcte"""
        if self.selected_option:
            self.is_correct = self.selected_option == self.question.correct_option
            self.points_earned = self.question.points if self.is_correct else 0
        super().save(*args, **kwargs)


# =====================
# Certificat (Certificate)
# =====================

class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issued_on = models.DateField(auto_now_add=True)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    certificate_number = models.CharField(max_length=50, unique=True, blank=True)

    class Meta:
        unique_together = ['student', 'course']

    def __str__(self):
        return f"Certificate for {self.student.username} in {self.course.title}"

    def save(self, *args, **kwargs):
        """Génère un numéro de certificat unique"""
        if not self.certificate_number:
            import uuid
            self.certificate_number = f"CERT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


# =====================
# Notification
# =====================

NOTIFICATION_TYPE_CHOICES = [
    ('enrollment', 'Inscription'),
    ('new_evaluation', 'Nouvelle Évaluation'),
    ('deadline_reminder', 'Rappel de Deadline'),
    ('grade_received', 'Note Reçue'),
    ('certificate_earned', 'Certificat Obtenu'),
    ('course_update', 'Mise à jour du Cours'),
    ('general', 'Général'),
]

NOTIFICATION_PRIORITY_CHOICES = [
    ('low', 'Basse'),
    ('medium', 'Moyenne'),
    ('high', 'Haute'),
]

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    sent_on = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    # Nouveaux champs pour catégorisation
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES, default='general')
    priority = models.CharField(max_length=10, choices=NOTIFICATION_PRIORITY_CHOICES, default='medium')
    
    # Liens vers les objets concernés
    related_course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL)
    related_evaluation = models.ForeignKey(Evaluation, null=True, blank=True, on_delete=models.SET_NULL)
    action_url = models.CharField(max_length=200, blank=True, help_text="URL vers l'action à effectuer")

    class Meta:
        ordering = ['-sent_on']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient.username} - {self.title}"


# =====================
# Modification de Cours (CourseModification)
# =====================

class CourseModification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    modified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-modified_at']

    def __str__(self):
        return f"{self.user.username} modified {self.course.title} at {self.modified_at.strftime('%Y-%m-%d %H:%M')}"
