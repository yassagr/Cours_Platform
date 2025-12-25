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

# =====================
# Module
# =====================

class Module(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# =====================
# Ressource (Resource)
# =====================
RESOURCE_TYPE_CHOICES = [
    ('video', 'video'),
    ('pdf', 'pdf'),
    ('image', 'image'),
    ('fichier', 'fichier'),
]

class Resource(models.Model):
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=50,choices=RESOURCE_TYPE_CHOICES)  # "video", "pdf", etc.
    file = models.FileField(upload_to='resources/')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="resources")

    def __str__(self):
        return self.title


# =====================
# Inscription (Enrollment)
# =====================

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_on = models.DateField(auto_now_add=True)
    certified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"

# =====================
# Progression (Progress)
# =====================

class Progress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="progresses")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="progresses")
    completion_percent = models.FloatField()
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.module.title} ({self.completion_percent}%)"

# =====================
# Évaluation (Evaluation)
# =====================

EVALUATION_TYPE_CHOICES = [
    ('Quiz', 'Quiz'),
    ('Assignment', 'Assignment'),
]

class Evaluation(models.Model):
    title = models.CharField(max_length=200)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='evaluations')
    evaluation_type = models.CharField(max_length=10, choices=EVALUATION_TYPE_CHOICES)
    deadline = models.DateField()

    def __str__(self):
        return self.title

# =====================
# Question
# =====================

class Question(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])

    def __str__(self):
        return self.text

# =====================
# Soumission (Submission)
# =====================

class Submission(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    submitted_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} submitted {self.evaluation.title}"

# =====================
# Réponse Soumise (SubmittedAnswer)
# =====================

class SubmittedAnswer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='submitted_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    total_score = models.IntegerField()


    def __str__(self):
        return f"Answer for {self.question.text} by {self.submission.student.username}"

# =====================
# Certificat (Certificate)
# =====================

class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issued_on = models.DateField(auto_now_add=True)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)


    def __str__(self):
        return f"Certificate for {self.student.username} in {self.course.title}"

# =====================
# Notification
# =====================

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    sent_on = models.DateField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.recipient.username} - {self.title}"



class CourseModification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    modified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} modified {self.course.title} at {self.modified_at.strftime('%Y-%m-%d %H:%M')}"
