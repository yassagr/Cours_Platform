from django.contrib import admin
from .models import *

# ------------------------------------------------------
# 1. Personnalisation de l'admin pour le modèle `User`
# ------------------------------------------------------
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'date_joined', 'last_login', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('role', 'is_active', 'is_staff')
    ordering = ('-date_joined',)  # Trier les utilisateurs par date d'inscription, du plus récent au plus ancien
    list_per_page = 20  # Afficher 20 utilisateurs par page

    actions = ['make_inactive', 'make_active']
    
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Marquer comme inactif"
    
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Marquer comme actif"

# Enregistrer le modèle `User` avec ces personnalisations
admin.site.register(User, UserAdmin)


# ------------------------------------------------------
# 2. Personnalisation de l'admin pour le modèle `Course`
# ------------------------------------------------------
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'level', 'start_date', 'end_date', 'estimated_duration')
    search_fields = ['title', 'instructor__username']
    list_filter = ('level', 'start_date', 'end_date')
    ordering = ('-start_date',)  # Trier les cours par date de début, du plus récent au plus ancien
    list_per_page = 10  # Afficher 10 cours par page
    date_hierarchy = 'start_date'  # Permet de filtrer par date

# Enregistrer le modèle `Course` avec ces personnalisations
admin.site.register(Course, CourseAdmin)


# ------------------------------------------------------
# 3. Personnalisation de l'admin pour le modèle `Module`
# ------------------------------------------------------
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'description')
    search_fields = ['title', 'course__title']
    list_filter = ('course',)
    ordering = ('title',)  # Trier par titre de module par défaut
    list_per_page = 15  # Afficher 15 modules par page

# Enregistrer le modèle `Module` avec ces personnalisations
admin.site.register(Module, ModuleAdmin)


# ------------------------------------------------------
# 4. Personnalisation de l'admin pour le modèle `Enrollment`
# ------------------------------------------------------
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_on', 'certified')
    search_fields = ['student__username', 'course__title']
    list_filter = ('certified', 'course', 'enrolled_on')
    ordering = ('-enrolled_on',)  # Trier par date d'inscription (du plus récent au plus ancien)
    list_per_page = 20  # Afficher 20 inscriptions par page

# Enregistrer le modèle `Enrollment` avec ces personnalisations
admin.site.register(Enrollment, EnrollmentAdmin)


# ------------------------------------------------------
# 5. Personnalisation de l'admin pour le modèle `Evaluation`
# ------------------------------------------------------
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'evaluation_type', 'deadline')
    search_fields = ['title', 'module__title']
    list_filter = ('evaluation_type', 'module', 'deadline')
    ordering = ('-deadline',)  # Trier par date limite (du plus récent au plus ancien)
    list_per_page = 15  # Afficher 15 évaluations par page

# Enregistrer le modèle `Evaluation` avec ces personnalisations
admin.site.register(Evaluation, EvaluationAdmin)


# ------------------------------------------------------
# 6. Personnalisation pour Resource
# ------------------------------------------------------
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'resource_type', 'has_url', 'has_file')
    search_fields = ['title', 'module__title', 'module__course__title']
    list_filter = ('resource_type', 'module__course')
    ordering = ('module', 'title')
    list_per_page = 20
    
    def has_url(self, obj):
        return bool(obj.url)
    has_url.boolean = True
    has_url.short_description = 'URL?'
    
    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = 'Fichier?'

admin.site.register(Resource, ResourceAdmin)


# ------------------------------------------------------
# 7. Personnalisation pour Question
# ------------------------------------------------------
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'evaluation', 'correct_option', 'points', 'order')
    search_fields = ['text', 'evaluation__title']
    list_filter = ('evaluation', 'correct_option')
    ordering = ('evaluation', 'order')
    list_per_page = 20
    
    def text_preview(self, obj):
        return obj.text[:60] + "..." if len(obj.text) > 60 else obj.text
    text_preview.short_description = 'Question'

admin.site.register(Question, QuestionAdmin)


# ------------------------------------------------------
# 8. Personnalisation pour Submission
# ------------------------------------------------------
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'evaluation', 'submitted_on', 'status', 'score', 'passed', 'attempt_number')
    search_fields = ['student__username', 'evaluation__title']
    list_filter = ('status', 'passed', 'evaluation__evaluation_type', 'submitted_on')
    ordering = ('-submitted_on',)
    list_per_page = 25
    readonly_fields = ('submitted_on', 'graded_on')

admin.site.register(Submission, SubmissionAdmin)


# ------------------------------------------------------
# 9. Personnalisation pour Certificate
# ------------------------------------------------------
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_number', 'student', 'course', 'issued_on', 'has_url', 'has_file')
    search_fields = ['certificate_number', 'student__username', 'course__title']
    list_filter = ('issued_on', 'course')
    ordering = ('-issued_on',)
    list_per_page = 20
    readonly_fields = ('certificate_number', 'issued_on')
    
    def has_url(self, obj):
        return bool(obj.certificate_url)
    has_url.boolean = True
    has_url.short_description = 'URL?'
    
    def has_file(self, obj):
        return bool(obj.certificate_file)
    has_file.boolean = True
    has_file.short_description = 'Fichier?'

admin.site.register(Certificate, CertificateAdmin)


# ------------------------------------------------------
# 10. Personnalisation pour Notification
# ------------------------------------------------------
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'priority', 'is_read', 'sent_on')
    search_fields = ['title', 'message', 'recipient__username']
    list_filter = ('notification_type', 'priority', 'is_read', 'sent_on')
    ordering = ('-sent_on',)
    list_per_page = 25
    readonly_fields = ('sent_on',)
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Marquer comme lu"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "Marquer comme non lu"

admin.site.register(Notification, NotificationAdmin)


# ------------------------------------------------------
# Modèles restants avec registration simple
# ------------------------------------------------------
admin.site.register(Progress)
admin.site.register(SubmittedAnswer)


# Personnalisation du site admin
admin.site.site_header = "EduSphere Administration"
admin.site.site_title = "EduSphere Admin"
admin.site.index_title = "Bienvenue dans l'administration EduSphere"
