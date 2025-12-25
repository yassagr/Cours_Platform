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


admin.site.register(Resource)
admin.site.register(Progress)
admin.site.register(Question)
admin.site.register(Submission)
admin.site.register(SubmittedAnswer)
admin.site.register(Certificate)
admin.site.register(Notification)
