from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View,TemplateView
from django.urls import reverse_lazy
from .models import *
from .forms import CourseForm, EvaluationForm
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django import forms
from django.core.exceptions import PermissionDenied




# Mixins pour contrôle d'accès
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'Admin'

class InstructorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'Instructor'
    
class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'Student'

class AdminOrInstructorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['Admin', 'Instructor']




# Vues pour Course
class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9  # Pagination: 9 cours par page (grille 3x3)
    
    def get_queryset(self):
        """Optimiser les requêtes avec select_related et prefetch_related"""
        return Course.objects.select_related('instructor').prefetch_related('modules', 'enrollments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated and user.role == 'Student':
            # Récupérer les IDs des cours déjà suivis
            enrolled_course_ids = Enrollment.objects.filter(student=user).values_list('course_id', flat=True)
            context['enrolled_course_ids'] = set(enrolled_course_ids)
        else:
            context['enrolled_course_ids'] = set()

        return context



class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        modules = course.modules.all()
        context['modules'] = modules

        # Logique du module sélectionné
        selected_module_id = self.request.GET.get('module_id')
        if selected_module_id:
            selected_module = get_object_or_404(Module, pk=selected_module_id, course=course)
        elif modules:
            selected_module = modules[0]
        else:
            selected_module = None

        context['selected_module'] = selected_module

        # Vérification d'inscription pour les étudiants
        if self.request.user.is_authenticated and self.request.user.role == 'Student':
            context['already_enrolled'] = Enrollment.objects.filter(
                student=self.request.user,
                course=self.object
            ).exists()
        else:
            context['already_enrolled'] = False

        return context


class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('course-list')


    def form_valid(self, form):
        form.instance.instructor = self.request.user  # assigner user avant la sauvegarde
        response = super().form_valid(form)           # sauvegarde form et obtient response
        # enregistrer la modification après la sauvegarde
        CourseModification.objects.create(
            user=self.request.user,
            course=self.object,
            description=f"Created course '{self.object.title}'"
        )
        return response



class CourseUpdateView(LoginRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('course-list')

    def dispatch(self, request, *args, **kwargs):
        course = self.get_object()
        if request.user.role == 'Admin' or course.instructor  == request.user:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied("You are not allowed to edit this course.")
        
    def form_valid(self, form):
        form.instance.instructor = self.request.user  # assigner user avant la sauvegarde
        response = super().form_valid(form)           # sauvegarde form et obtient response
        # enregistrer la modification après la sauvegarde
        CourseModification.objects.create(
            user=self.request.user,
            course=self.object,
            description=f"Updated course '{self.object.title}'"
        )
        return response

class CourseDeleteView(LoginRequiredMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('course-list')


    def dispatch(self, request, *args, **kwargs):
        course = self.get_object()
        if request.user.role == 'Admin' or course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied("You are not allowed to delete this course.")
        
    



# Vues pour Module


class ModuleListView(LoginRequiredMixin, View):
    def get(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        modules = list(course.modules.all())
        
        # Ajouter la progression pour chaque module si l'utilisateur est étudiant inscrit
        if request.user.role == 'Student':
            try:
                enrollment = Enrollment.objects.get(student=request.user, course=course)
                for module in modules:
                    # Chercher la progression du module pour cet étudiant
                    progress = Progress.objects.filter(
                        enrollment=enrollment,
                        module=module
                    ).first()
                    
                    if progress:
                        module.progress_percent = progress.completion_percent
                    else:
                        # Calculer manuellement si pas de Progress enregistré
                        total_resources = module.resources.count()
                        total_evals = module.evaluations.count()
                        
                        if total_resources + total_evals > 0:
                            # Compter les évaluations passées
                            passed_evals = Submission.objects.filter(
                                student=request.user,
                                evaluation__module=module,
                                passed=True
                            ).values('evaluation').distinct().count()
                            
                            progress_value = (passed_evals / (total_resources + total_evals)) * 100 if total_evals > 0 else 0
                            module.progress_percent = min(progress_value, 100)
                        else:
                            module.progress_percent = 0
            except Enrollment.DoesNotExist:
                # Pas inscrit, pas de progression
                for module in modules:
                    module.progress_percent = None
        else:
            # Instructeur/Admin - pas de progression individuelle
            for module in modules:
                module.progress_percent = None
        
        selected_module_id = request.GET.get('module_id')
        selected_module = None
        resources = []
        evaluations = []

        if selected_module_id:
            selected_module = get_object_or_404(Module, pk=selected_module_id, course=course)
        elif modules:
            selected_module = modules[0]  # par défaut le premier module

        if selected_module:
            resources = selected_module.resources.all()
            evaluations = selected_module.evaluations.all()

        # Récupérer les IDs des ressources consultées par l'étudiant
        viewed_resource_ids = []
        if request.user.role == 'Student':
            viewed_resource_ids = list(
                ResourceView.objects.filter(
                    student=request.user,
                    resource__module__course=course
                ).values_list('resource_id', flat=True)
            )

        return render(request, 'modules/module_list.html', {
            'course': course,
            'modules': modules,
            'selected_module': selected_module,
            'resources': resources,
            'evaluations': evaluations,
            'viewed_resource_ids': viewed_resource_ids,
        })


class ModuleCreateView(AdminOrInstructorRequiredMixin, CreateView):
    model = Module
    fields = ['title', 'description']
    template_name = 'modules/module_form.html'

    def form_valid(self, form):
        course_id = self.kwargs['course_id']
        form.instance.course = get_object_or_404(Course, pk=course_id)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('module-list-by-course', kwargs={'course_id': self.object.course.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs['course_id']
        context['course'] = get_object_or_404(Course, pk=course_id)
        return context
    
    def dispatch(self, request, *args, **kwargs):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, pk=course_id)

        if request.user.role == 'Admin' or course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)
        
        raise PermissionDenied("You can't create a module for this course.")



class ModuleUpdateView(AdminOrInstructorRequiredMixin, UpdateView):
    model = Module
    fields = ['title', 'description']
    template_name = 'modules/module_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        return context
    
    def get_success_url(self):
        return reverse_lazy('module-list-by-course', kwargs={'course_id': self.object.course.id})
    
    def dispatch(self, request, *args, **kwargs):
        module = self.get_object()
        # Vérifie que l'utilisateur est admin ou que le professeur est bien l'instructeur du cours lié
        if request.user.role == 'Admin' or module.course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied("You can't modify module.")


class ModuleDeleteView(AdminOrInstructorRequiredMixin, DeleteView):
    model = Module
    template_name = 'modules/module_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        return context

    def get_success_url(self):
        return reverse_lazy('module-list-by-course', kwargs={'course_id': self.object.course.id})
    
    def dispatch(self, request, *args, **kwargs):
        module = self.get_object()
        # Vérifie que l'utilisateur est admin ou que le professeur est bien l'instructeur du cours lié
        if request.user.role == 'Admin' or module.course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied("You can't delete module.")


# Vues pour Resource

class ResourceCreateView(AdminOrInstructorRequiredMixin, CreateView):
    model = Resource
    fields = ['title', 'resource_type', 'file']
    template_name = 'resources/resource_form.html'

    def form_valid(self, form):
        module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        form.instance.module = module
        response = super().form_valid(form)
        
        # Notifier tous les étudiants inscrits
        course = module.course
        enrolled_students = User.objects.filter(
            enrollments__course=course,
            role='Student'
        )
        
        for student in enrolled_students:
            create_notification(
                recipient=student,
                title="Nouvelle ressource disponible",
                message=f"Une nouvelle ressource '{self.object.title}' a été ajoutée au module '{module.title}' du cours '{course.title}'.",
                notif_type='course_update',
                related_course=course,
                action_url=f"/modules/course/{course.id}/?module_id={module.id}",
                priority='medium'
            )
        
        messages.success(
            self.request, 
            f"Ressource ajoutée. {enrolled_students.count()} étudiant(s) notifié(s)."
        )
        return response

    def get_success_url(self):
        return reverse_lazy('module-list-by-course', kwargs={'course_id': self.object.module.course.id})

    def get_initial(self):
        module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        return {'module': module}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        context['module'] = module
        context['course'] = module.course
        return context
    
    def dispatch(self, request, *args, **kwargs):
        module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        course = module.course
        if request.user.role == 'Admin' or course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied("You can't add a resource to this module.")
    
    

class ResourceUpdateView(AdminOrInstructorRequiredMixin, UpdateView):
    model = Resource
    fields = ['title', 'resource_type', 'file']
    template_name = 'resources/resource_form.html'

    def get_success_url(self):
        module = self.object.module
        course_id = module.course.id if module and module.course else None
        return reverse_lazy('module-list-by-course', kwargs={'course_id': course_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource = self.object
        context['module'] = resource.module
        context['course'] = resource.module.course  # pour ton template
        return context
    
    def dispatch(self, request, *args, **kwargs):
        # Récupérer manuellement l'objet sans utiliser self.get_object()
        resource = get_object_or_404(Resource, pk=self.kwargs['pk'])
        course = resource.module.course

        if request.user.role == 'Admin' or course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("You can't modify this resource.")


class ResourceDeleteView(AdminOrInstructorRequiredMixin, DeleteView):
    model = Resource
    template_name = 'resources/resource_confirm_delete.html'

    def get_success_url(self):
        module = self.object.module
        course_id = module.course.id if module and module.course else None
        return reverse_lazy('module-list-by-course', kwargs={'course_id': course_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource = self.object
        context['module'] = resource.module
        context['course'] = resource.module.course  # pour ton template
        return context
    
    def dispatch(self, request, *args, **kwargs):
        resource = self.get_object()
        # Vérifie que l'utilisateur est admin ou que le professeur est bien l'instructeur du cours lié
        if request.user.role == 'Admin' or resource.module.course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied("You can't delete recource.")
    


# Vues pour Evaluation

class EvaluationCreateView(AdminOrInstructorRequiredMixin, CreateView):
    model = Evaluation
    form_class = EvaluationForm
    template_name = 'evaluations/evaluation_form.html'

    def form_valid(self, form):
        module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        form.instance.module = module
        response = super().form_valid(form)
        
        # Notifier tous les étudiants inscrits
        course = module.course
        enrolled_students = User.objects.filter(
            enrollments__course=course,
            role='Student'
        )
        
        eval_type = "quiz" if self.object.evaluation_type == 'quiz' else "devoir"
        
        for student in enrolled_students:
            create_notification(
                recipient=student,
                title=f"Nouveau {eval_type} disponible",
                message=f"Un nouveau {eval_type} '{self.object.title}' a été ajouté au cours '{course.title}'. Date limite: {self.object.deadline}.",
                notif_type='new_evaluation',
                related_course=course,
                related_evaluation=self.object,
                action_url=f"/modules/course/{course.id}/?module_id={module.id}",
                priority='high'
            )
        
        messages.success(
            self.request, 
            f"Évaluation créée. {enrolled_students.count()} étudiant(s) notifié(s)."
        )
        return response

    def get_success_url(self):
        return reverse_lazy('module-list-by-course', kwargs={'course_id': self.object.module.course.id})

    def get_initial(self):
        module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        return {'module': module}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        context['module'] = module
        context['course'] = module.course
        return context
    
    def dispatch(self, request, *args, **kwargs):
        # Récupérer le module pour vérifier les permissions
        module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        course = module.course

        if request.user.role == 'Admin' or course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("You can't create this evaluation.")



class EvaluationUpdateView(AdminOrInstructorRequiredMixin, UpdateView):
    model = Evaluation
    form_class = EvaluationForm
    template_name = 'evaluations/evaluation_form.html'

    def get_success_url(self):
        module = self.object.module
        course_id = module.course.id if module and module.course else None
        return reverse_lazy('module-list-by-course', kwargs={'course_id': course_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evaluation = self.object
        context['module'] = evaluation.module
        context['course'] = evaluation.module.course
        return context
    
    def dispatch(self, request, *args, **kwargs):
        evaluation = self.get_object()
        # Vérifie que l'utilisateur est admin ou que le professeur est bien l'instructeur du cours lié
        if request.user.role == 'Admin' or evaluation.module.course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied("You can't modify recource.")


class EvaluationDeleteView(AdminOrInstructorRequiredMixin, DeleteView):
    model = Evaluation
    template_name = 'evaluations/evaluation_confirm_delete.html'

    def get_success_url(self):
        module = self.object.module
        course_id = module.course.id if module and module.course else None
        return reverse_lazy('module-list-by-course', kwargs={'course_id': course_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evaluation = self.object
        context['module'] = evaluation.module
        context['course'] = evaluation.module.course
        return context
    
    def dispatch(self, request, *args, **kwargs):
        evaluation = self.get_object()
        # Vérifie que l'utilisateur est admin ou que le professeur est bien l'instructeur du cours lié
        if request.user.role == 'Admin' or evaluation.module.course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied("You can't delete recource.")



User = get_user_model()

class SignUpView(View):
    def get(self, request):
        return render(request, 'registration/signup.html')

    def post(self, request):
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        role = request.POST.get('role')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'registration/signup.html')

        if role not in ['Student', 'Instructor']:
            messages.error(request, "Invalid role selected.")
            return render(request, 'registration/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'registration/signup.html')

        user = User.objects.create_user(username=username, email=email, password=password1, role=role)
        messages.success(request, "Account created successfully. You can now log in.")
        return redirect('login')  
    


class EnrollView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        course = get_object_or_404(Course, pk=pk)
        
        # Vérifie que l'utilisateur est étudiant
        if request.user.role != 'Student':
            messages.error(request, "Seuls les étudiants peuvent s'inscrire aux cours.")
            return redirect('course-detail', pk=pk)

        # Vérifie si déjà inscrit
        already_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        if already_enrolled:
            messages.info(request, "Vous êtes déjà inscrit à ce cours.")
        else:
            Enrollment.objects.create(student=request.user, course=course)
            messages.success(request, "Inscription réussie!")
            
            # =====================================================
            # SYNC NEO4J: Créer relation ENROLLED_IN
            # =====================================================
            try:
                from base.neo_models import NeoUser, NeoCourse, get_neo_user
                from datetime import date
                
                neo_user = get_neo_user(request)
                if neo_user:
                    # Trouver le cours Neo4j par titre
                    neo_course = NeoCourse.nodes.get_or_none(title=course.title)
                    if neo_course:
                        # Créer la relation si pas déjà existante
                        if neo_course not in neo_user.enrolled_in.all():
                            neo_user.enrolled_in.connect(neo_course, {
                                'enrolled_on': date.today(),
                                'completion_percent': 0.0,
                                'certified': False
                            })
                            import logging
                            logger = logging.getLogger('base')
                            logger.info(f"Neo4j: {request.user.username} enrolled in {course.title}")
            except Exception as e:
                import logging
                logger = logging.getLogger('base')
                logger.warning(f"Neo4j enrollment sync failed: {e}")
            # =====================================================
            
            # Notifier l'instructeur de la nouvelle inscription
            create_notification(
                recipient=course.instructor,
                title="Nouvelle inscription",
                message=f"{request.user.get_full_name() or request.user.username} s'est inscrit au cours '{course.title}'.",
                notif_type='enrollment',
                related_course=course,
                action_url=f"/courses/{course.id}/",
                priority='low'
            )

        return redirect('course-detail', pk=pk)
    
    
    
class UnenrollView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        course = get_object_or_404(Course, pk=pk)

        # Vérifie que l'utilisateur est étudiant
        if request.user.role != 'Student':
            messages.error(request, "Only students can unenroll from courses.")
            return redirect('course-detail', pk=pk)

        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        if enrollment:
            enrollment.delete()
            messages.success(request, "You have successfully unenrolled from the course.")
            
            # =====================================================
            # SYNC NEO4J: Supprimer relation ENROLLED_IN
            # =====================================================
            try:
                from base.neo_models import NeoUser, NeoCourse, get_neo_user
                
                neo_user = get_neo_user(request)
                if neo_user:
                    neo_course = NeoCourse.nodes.get_or_none(title=course.title)
                    if neo_course and neo_course in neo_user.enrolled_in.all():
                        neo_user.enrolled_in.disconnect(neo_course)
                        import logging
                        logger = logging.getLogger('base')
                        logger.info(f"Neo4j: {request.user.username} unenrolled from {course.title}")
            except Exception as e:
                import logging
                logger = logging.getLogger('base')
                logger.warning(f"Neo4j unenroll sync failed: {e}")
            # =====================================================
        else:
            messages.info(request, "You are not enrolled in this course.")

        return redirect('course-detail', pk=pk)
    



class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']  # ne modifie pas le rôle ici

class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'students/dashboard.html'

    def get_neo_recommendations(self, user):
        """Récupérer les recommandations depuis Neo4j"""
        try:
            from base.recommendations import CourseRecommendationEngine
            recommendations = CourseRecommendationEngine.get_recommendations_for_student(
                user.username, limit=6
            )
            return recommendations
        except Exception as e:
            import logging
            logger = logging.getLogger('base')
            logger.warning(f"Neo4j recommendations failed: {e}")
            return []

    def get(self, request, *args, **kwargs):
        user = request.user
        form = UserUpdateForm(instance=user)

        # Cours où il est inscrit (Django ORM pour compatibilité)
        enrolled_courses = Course.objects.filter(enrollments__student=user)

        # Cours non inscrits pour suggestions (fallback)
        suggested_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))[:6]

        # Recommandations intelligentes Neo4j
        neo_recommendations = self.get_neo_recommendations(user)

        # Certificats
        certificates = Certificate.objects.filter(student=user)

        context = {
            'form': form,
            'enrolled_courses': enrolled_courses,
            'suggested_courses': suggested_courses,
            'neo_recommendations': neo_recommendations,  # Recommandations Neo4j
            'certificates': certificates,
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        user = request.user
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('student-dashboard')
        else:
            messages.error(request, "Please correct the errors below.")

        # Même contexte que get
        enrolled_courses = Course.objects.filter(enrollments__student=user)
        suggested_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))[:6]
        neo_recommendations = self.get_neo_recommendations(user)
        certificates = Certificate.objects.filter(student=user)

        context = {
            'form': form,
            'enrolled_courses': enrolled_courses,
            'suggested_courses': suggested_courses,
            'neo_recommendations': neo_recommendations,
            'certificates': certificates,
        }
        return self.render_to_response(context)
    


class TeacherDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'teachers/dashboard.html'

    def get(self, request, *args, **kwargs):
        return self.render_dashboard(request)

    def post(self, request, *args, **kwargs):
        user = request.user
        form = UserUpdateForm(request.POST, instance=user)

        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('teacher-dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
            return self.render_dashboard(request, form=form)

    def render_dashboard(self, request, form=None):
        user = request.user
        if not form:
            form = UserUpdateForm(instance=user)

        created_courses = Course.objects.filter(instructor=user)
        last_modifications = CourseModification.objects.filter(user=user).order_by('-modified_at')[:10]

        enrolled_users_by_course = {
            course: [enroll.student for enroll in Enrollment.objects.filter(course=course)]
            for course in created_courses
        }

        context = {
            'form': form,
            'created_courses': created_courses,
            'last_modifications': last_modifications,
            'enrolled_users_by_course': enrolled_users_by_course,
        }
        return self.render_to_response(context)


# =====================================================
# QUESTIONS - CRUD Views
# =====================================================

class QuestionListView(LoginRequiredMixin, View):
    """Liste des questions d'une évaluation"""
    def get(self, request, evaluation_id):
        evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
        course = evaluation.module.course
        
        # Vérifier les permissions
        if not (request.user.role == 'Admin' or course.instructor == request.user):
            raise PermissionDenied("Vous n'avez pas accès à cette évaluation.")
        
        questions = evaluation.questions.all()
        
        return render(request, 'questions/question_list.html', {
            'evaluation': evaluation,
            'questions': questions,
            'course': course,
            'module': evaluation.module,
        })


class QuestionCreateView(AdminOrInstructorRequiredMixin, CreateView):
    """Ajouter une question à une évaluation"""
    model = Question
    fields = ['text', 'option1', 'option2', 'option3', 'option4', 'correct_option', 'points']
    template_name = 'questions/question_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.evaluation = get_object_or_404(Evaluation, pk=self.kwargs['evaluation_id'])
        course = self.evaluation.module.course
        if not (request.user.role == 'Admin' or course.instructor == request.user):
            raise PermissionDenied("Vous ne pouvez pas ajouter de questions à cette évaluation.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.evaluation = self.evaluation
        form.instance.order = self.evaluation.questions.count() + 1
        messages.success(self.request, "Question ajoutée avec succès!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('question-list', kwargs={'evaluation_id': self.evaluation.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evaluation'] = self.evaluation
        context['course'] = self.evaluation.module.course
        context['is_edit'] = False
        return context


class QuestionUpdateView(AdminOrInstructorRequiredMixin, UpdateView):
    """Modifier une question"""
    model = Question
    fields = ['text', 'option1', 'option2', 'option3', 'option4', 'correct_option', 'points']
    template_name = 'questions/question_form.html'

    def dispatch(self, request, *args, **kwargs):
        question = self.get_object()
        course = question.evaluation.module.course
        if not (request.user.role == 'Admin' or course.instructor == request.user):
            raise PermissionDenied("Vous ne pouvez pas modifier cette question.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Question modifiée avec succès!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('question-list', kwargs={'evaluation_id': self.object.evaluation.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evaluation'] = self.object.evaluation
        context['course'] = self.object.evaluation.module.course
        context['is_edit'] = True
        return context


class QuestionDeleteView(AdminOrInstructorRequiredMixin, DeleteView):
    """Supprimer une question"""
    model = Question
    template_name = 'questions/question_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        question = self.get_object()
        course = question.evaluation.module.course
        if not (request.user.role == 'Admin' or course.instructor == request.user):
            raise PermissionDenied("Vous ne pouvez pas supprimer cette question.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Question supprimée avec succès!")
        return reverse_lazy('question-list', kwargs={'evaluation_id': self.object.evaluation.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evaluation'] = self.object.evaluation
        context['course'] = self.object.evaluation.module.course
        return context


# =====================================================
# QUIZ - Take, Submit, Results Views
# =====================================================

class QuizTakeView(LoginRequiredMixin, View):
    """Affiche le quiz pour qu'un étudiant le passe"""
    def get(self, request, pk):
        evaluation = get_object_or_404(Evaluation, pk=pk)
        course = evaluation.module.course
        
        # Vérifier que c'est un Quiz
        if evaluation.evaluation_type != 'Quiz':
            messages.error(request, "Cette évaluation n'est pas un quiz.")
            return redirect('module-list-by-course', course_id=course.id)
        
        # Vérifier l'inscription de l'étudiant
        if request.user.role == 'Student':
            enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
            if not enrolled:
                messages.error(request, "Vous devez être inscrit au cours pour passer ce quiz.")
                return redirect('course-detail', pk=course.id)
        
        # Vérifier les tentatives précédentes
        previous_submissions = Submission.objects.filter(
            evaluation=evaluation, 
            student=request.user
        ).order_by('-attempt_number')
        
        if previous_submissions.exists():
            last_attempt = previous_submissions.first()
            if not evaluation.allow_retake:
                messages.info(request, "Vous avez déjà passé ce quiz. Les reprises ne sont pas autorisées.")
                return redirect('quiz-results', pk=last_attempt.id)
            if last_attempt.attempt_number >= evaluation.max_attempts:
                messages.info(request, f"Vous avez atteint le nombre maximum de tentatives ({evaluation.max_attempts}).")
                return redirect('quiz-results', pk=last_attempt.id)
        
        questions = evaluation.questions.all()
        if not questions.exists():
            messages.warning(request, "Ce quiz ne contient pas encore de questions.")
            return redirect('module-list-by-course', course_id=course.id)
        
        return render(request, 'evaluations/take_quiz.html', {
            'evaluation': evaluation,
            'questions': questions,
            'course': course,
            'previous_attempts': previous_submissions.count(),
            'max_attempts': evaluation.max_attempts,
        })


class QuizSubmitView(LoginRequiredMixin, View):
    """Traite la soumission d'un quiz et calcule le score"""
    def post(self, request, pk):
        evaluation = get_object_or_404(Evaluation, pk=pk)
        course = evaluation.module.course
        
        # Vérifications de sécurité
        if evaluation.evaluation_type != 'Quiz':
            messages.error(request, "Cette évaluation n'est pas un quiz.")
            return redirect('module-list-by-course', course_id=course.id)
        
        # Calculer le numéro de tentative
        previous_count = Submission.objects.filter(
            evaluation=evaluation, 
            student=request.user
        ).count()
        
        # Créer la soumission
        from django.utils import timezone
        submission = Submission.objects.create(
            evaluation=evaluation,
            student=request.user,
            attempt_number=previous_count + 1,
            status='graded',
            graded_on=timezone.now()
        )
        
        # Traiter chaque réponse
        questions = evaluation.questions.all()
        total_points = 0
        earned_points = 0
        
        for question in questions:
            answer_key = f'question_{question.id}'
            selected_option = request.POST.get(answer_key, '').strip()
            
            # Distinguer "pas de réponse" vs "mauvaise réponse"
            if not selected_option:
                # Question non répondue
                SubmittedAnswer.objects.create(
                    submission=submission,
                    question=question,
                    selected_option=None,
                    is_correct=False,
                    points_earned=0
                )
            else:
                # Réponse fournie
                is_correct = selected_option == question.correct_option
                points = question.points if is_correct else 0
                
                SubmittedAnswer.objects.create(
                    submission=submission,
                    question=question,
                    selected_option=selected_option,
                    is_correct=is_correct,
                    points_earned=points
                )
                earned_points += points
            
            total_points += question.points
        
        # Calculer et sauvegarder le score
        submission.score = earned_points
        submission.max_score = total_points
        submission.percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        submission.passed = submission.percentage >= evaluation.passing_score
        submission.save()
        
        # Mettre à jour la progression du cours et vérifier le certificat
        if submission.passed:
            try:
                enrollment = Enrollment.objects.get(student=request.user, course=course)
                update_course_progress(enrollment)
            except Enrollment.DoesNotExist:
                pass
        
        # Créer une notification
        create_notification(
            recipient=request.user,
            title="Quiz terminé!",
            message=f"Vous avez obtenu {submission.percentage:.1f}% au quiz '{evaluation.title}'.",
            notif_type='grade_received',
            related_course=course,
            related_evaluation=evaluation,
            action_url=f"/submission/{submission.id}/results/"
        )
        
        messages.success(request, f"Quiz soumis! Score: {earned_points}/{total_points} ({submission.percentage:.1f}%)")
        return redirect('quiz-results', pk=submission.id)


class QuizResultView(LoginRequiredMixin, View):
    """Affiche les résultats d'un quiz après soumission"""
    def get(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk)
        evaluation = submission.evaluation
        course = evaluation.module.course
        
        # Vérifier les permissions (l'étudiant voit ses résultats, l'instructeur voit tout)
        if request.user != submission.student:
            if not (request.user.role == 'Admin' or course.instructor == request.user):
                raise PermissionDenied("Vous n'avez pas accès à ces résultats.")
        
        answers = submission.submitted_answers.select_related('question').all()
        
        return render(request, 'evaluations/quiz_results.html', {
            'submission': submission,
            'evaluation': evaluation,
            'answers': answers,
            'course': course,
            'show_corrections': evaluation.show_correct_answers,
        })


# =====================================================
# ASSIGNMENTS - Submit, List, Grade Views
# =====================================================

class AssignmentSubmitView(LoginRequiredMixin, View):
    """Soumettre un devoir (Assignment)"""
    def get(self, request, pk):
        evaluation = get_object_or_404(Evaluation, pk=pk)
        course = evaluation.module.course
        
        if evaluation.evaluation_type != 'Assignment':
            messages.error(request, "Cette évaluation n'est pas un devoir.")
            return redirect('module-list-by-course', course_id=course.id)
        
        # Vérifier l'inscription
        enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        if not enrolled:
            messages.error(request, "Vous devez être inscrit au cours.")
            return redirect('course-detail', pk=course.id)
        
        # Vérifier si déjà soumis
        existing = Submission.objects.filter(evaluation=evaluation, student=request.user).first()
        
        return render(request, 'evaluations/submit_assignment.html', {
            'evaluation': evaluation,
            'course': course,
            'existing_submission': existing,
        })

    def post(self, request, pk):
        evaluation = get_object_or_404(Evaluation, pk=pk)
        course = evaluation.module.course
        
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, "Veuillez sélectionner un fichier.")
            return redirect('assignment-submit', pk=pk)
        
        # Vérifier la taille du fichier (max 10 MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            messages.error(request, "Le fichier est trop volumineux (max 10 MB).")
            return redirect('assignment-submit', pk=pk)
        
        from django.utils import timezone
        
        # Créer ou mettre à jour la soumission
        submission, created = Submission.objects.update_or_create(
            evaluation=evaluation,
            student=request.user,
            attempt_number=1,
            defaults={
                'file': uploaded_file,
                'status': 'pending',
                'submitted_on': timezone.now()
            }
        )
        
        # Vérifier si soumis en retard (comparaison robuste avec fuseau horaire)
        import datetime
        deadline_end = timezone.make_aware(
            datetime.datetime.combine(evaluation.deadline, datetime.time.max)
        ) if evaluation.deadline else None
        
        if deadline_end and timezone.now() > deadline_end:
            submission.status = 'late'
            submission.save()
        
        # Notifier l'instructeur
        create_notification(
            recipient=course.instructor,
            title="Nouvelle soumission de devoir",
            message=f"{request.user.username} a soumis le devoir '{evaluation.title}'.",
            notif_type='enrollment',
            related_course=course,
            related_evaluation=evaluation,
            action_url=f"/evaluation/{evaluation.id}/submissions/"
        )
        
        messages.success(request, "Devoir soumis avec succès!")
        return redirect('module-list-by-course', course_id=course.id)


class SubmissionListView(AdminOrInstructorRequiredMixin, View):
    """Liste des soumissions pour une évaluation (vue instructeur)"""
    def get(self, request, evaluation_id):
        evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
        course = evaluation.module.course
        
        if not (request.user.role == 'Admin' or course.instructor == request.user):
            raise PermissionDenied("Accès non autorisé.")
        
        submissions = Submission.objects.filter(evaluation=evaluation).select_related('student').order_by('-submitted_on')
        
        graded_count = submissions.filter(status='graded').count()
        pending_count = submissions.exclude(status='graded').count()
        
        return render(request, 'evaluations/submission_list.html', {
            'evaluation': evaluation,
            'submissions': submissions,
            'course': course,
            'graded_count': graded_count,
            'pending_count': pending_count,
        })


class SubmissionGradeView(AdminOrInstructorRequiredMixin, View):
    """Noter une soumission de devoir"""
    def get(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk)
        course = submission.evaluation.module.course
        
        if not (request.user.role == 'Admin' or course.instructor == request.user):
            raise PermissionDenied("Accès non autorisé.")
        
        return render(request, 'evaluations/grade_submission.html', {
            'submission': submission,
            'evaluation': submission.evaluation,
            'course': course,
        })

    def post(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk)
        course = submission.evaluation.module.course
        
        if not (request.user.role == 'Admin' or course.instructor == request.user):
            raise PermissionDenied("Accès non autorisé.")
        
        try:
            score = float(request.POST.get('score', 0))
            max_score = submission.evaluation.max_score
            
            if score < 0 or score > max_score:
                messages.error(request, f"Le score doit être entre 0 et {max_score}.")
                return redirect('submission-grade', pk=pk)
            
            from django.utils import timezone
            
            submission.score = score
            submission.max_score = max_score
            submission.percentage = (score / max_score * 100) if max_score > 0 else 0
            submission.passed = submission.percentage >= submission.evaluation.passing_score
            submission.instructor_comment = request.POST.get('comment', '')
            submission.graded_on = timezone.now()
            submission.graded_by = request.user
            submission.status = 'graded'
            submission.save()
            
            # Notifier l'étudiant
            create_notification(
                recipient=submission.student,
                title="Note reçue",
                message=f"Votre devoir '{submission.evaluation.title}' a été noté: {score}/{max_score}.",
                notif_type='grade_received',
                related_course=course,
                related_evaluation=submission.evaluation,
                action_url=f"/submission/{submission.id}/results/",
                priority='high'
            )
            
            messages.success(request, "Soumission notée avec succès!")
            return redirect('submission-list', evaluation_id=submission.evaluation.id)
            
        except ValueError:
            messages.error(request, "Score invalide.")
            return redirect('submission-grade', pk=pk)


# =====================================================
# PROGRESS TRACKING
# =====================================================

class MarkResourceViewedView(LoginRequiredMixin, View):
    """Marquer une ressource comme consultée"""
    def get(self, request, pk):
        return self.mark_viewed(request, pk)
    
    def post(self, request, pk):
        return self.mark_viewed(request, pk)
    
    def mark_viewed(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        
        # Créer l'enregistrement de vue (ou ignorer si existe déjà)
        ResourceView.objects.get_or_create(
            student=request.user,
            resource=resource
        )
        
        # Mettre à jour la progression du module
        update_module_progress(request.user, resource.module)
        
        messages.success(request, f"Ressource '{resource.title}' marquée comme consultée!")
        
        return redirect(request.META.get('HTTP_REFERER', '/'))


def update_module_progress(user, module):
    """Met à jour la progression d'un utilisateur pour un module"""
    from django.utils import timezone
    
    course = module.course
    enrollment = Enrollment.objects.filter(student=user, course=course).first()
    
    if not enrollment:
        return
    
    # Calculer les ressources vues
    total_resources = module.resources.count()
    viewed_resources = ResourceView.objects.filter(
        student=user,
        resource__module=module
    ).count()
    
    # Calculer les évaluations complétées
    total_evaluations = module.evaluations.count()
    completed_evaluations = Submission.objects.filter(
        student=user,
        evaluation__module=module,
        status='graded'
    ).values('evaluation').distinct().count()
    
    # Calculer le pourcentage
    total_items = total_resources + total_evaluations
    completed_items = viewed_resources + completed_evaluations
    completion_percent = (completed_items / total_items * 100) if total_items > 0 else 0
    
    # Mettre à jour ou créer Progress
    progress, created = Progress.objects.update_or_create(
        enrollment=enrollment,
        module=module,
        defaults={
            'completion_percent': completion_percent,
            'resources_viewed': viewed_resources,
            'total_resources': total_resources,
            'evaluations_completed': completed_evaluations,
            'total_evaluations': total_evaluations,
            'is_completed': completion_percent >= 100,
            'completed_on': timezone.now() if completion_percent >= 100 else None,
        }
    )
    
    # Mettre à jour la progression du cours
    update_course_progress(enrollment)
    
    return progress


def update_course_progress(enrollment):
    """Met à jour la progression globale d'un cours"""
    course = enrollment.course
    total_modules = course.modules.count()
    
    if total_modules == 0:
        return
    
    # Calculer les modules complétés
    completed_modules = Progress.objects.filter(
        enrollment=enrollment,
        is_completed=True
    ).count()
    
    # Calculer le pourcentage moyen
    avg_completion = Progress.objects.filter(enrollment=enrollment).aggregate(
        avg=models.Avg('completion_percent')
    )['avg'] or 0
    
    # Score moyen des évaluations
    avg_score = Submission.objects.filter(
        student=enrollment.student,
        evaluation__module__course=course,
        status='graded'
    ).aggregate(avg=models.Avg('percentage'))['avg']
    
    # Mettre à jour CourseProgress
    CourseProgress.objects.update_or_create(
        enrollment=enrollment,
        defaults={
            'overall_completion_percent': avg_completion,
            'modules_completed': completed_modules,
            'total_modules': total_modules,
            'average_score': avg_score,
        }
    )
    
    # Vérifier si le cours est terminé pour générer un certificat
    if avg_completion >= 100 and not enrollment.certified:
        check_and_generate_certificate(enrollment)


def check_and_generate_certificate(enrollment):
    """Vérifie si l'étudiant peut recevoir un certificat et le génère"""
    # Vérifier que toutes les évaluations sont passées avec succès
    course = enrollment.course
    evaluations = Evaluation.objects.filter(module__course=course)
    
    for evaluation in evaluations:
        passed_submission = Submission.objects.filter(
            student=enrollment.student,
            evaluation=evaluation,
            passed=True
        ).exists()
        
        if not passed_submission:
            return None  # Pas encore prêt pour le certificat
    
    # Générer le certificat
    certificate, created = Certificate.objects.get_or_create(
        student=enrollment.student,
        course=course
    )
    
    if created:
        enrollment.certified = True
        enrollment.save()
        
        # Notification
        create_notification(
            recipient=enrollment.student,
            title="Certificat obtenu! 🎉",
            message=f"Félicitations! Vous avez obtenu le certificat pour '{course.title}'.",
            notif_type='certificate_earned',
            related_course=course,
            priority='high'
        )
    
    return certificate


# =====================================================
# NOTIFICATIONS
# =====================================================

def create_notification(recipient, title, message, notif_type='general', 
                       related_course=None, related_evaluation=None, 
                       action_url='', priority='medium'):
    """Fonction utilitaire pour créer des notifications"""
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notif_type,
        related_course=related_course,
        related_evaluation=related_evaluation,
        action_url=action_url,
        priority=priority
    )


class NotificationListView(LoginRequiredMixin, View):
    """Liste des notifications de l'utilisateur"""
    def get(self, request):
        notifications = Notification.objects.filter(recipient=request.user).order_by('-sent_on')
        unread_count = notifications.filter(is_read=False).count()
        
        return render(request, 'notifications/notification_list.html', {
            'notifications': notifications,
            'unread_count': unread_count,
        })


class NotificationMarkReadView(LoginRequiredMixin, View):
    """Marquer une notification comme lue"""
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.is_read = True
        notification.save()
        
        return redirect(notification.action_url if notification.action_url else 'notification-list')


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    """Marquer toutes les notifications comme lues"""
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, "Toutes les notifications ont été marquées comme lues.")
        return redirect('notification-list')


# =====================================================
# CONTEXT PROCESSOR pour les notifications (à ajouter dans settings.py)
# =====================================================

def notification_context(request):
    """Context processor pour afficher le compteur de notifications dans la navbar"""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}


# =====================================================
# CERTIFICATES
# =====================================================

class CertificateListView(LoginRequiredMixin, View):
    """Liste des certificats de l'utilisateur"""
    def get(self, request):
        certificates = Certificate.objects.filter(student=request.user).select_related('course')
        
        return render(request, 'certificates/certificate_list.html', {
            'certificates': certificates,
        })


class CertificateDownloadView(LoginRequiredMixin, View):
    """Télécharger un certificat en PDF"""
    def get(self, request, pk):
        certificate = get_object_or_404(Certificate, pk=pk)
        
        # Vérifier que l'utilisateur a le droit de télécharger
        if certificate.student != request.user:
            if not (request.user.role == 'Admin' or certificate.course.instructor == request.user):
                raise PermissionDenied("Vous n'avez pas accès à ce certificat.")
        
        # Importer la fonction de génération
        from .utils import generate_certificate_pdf
        
        # Générer le PDF
        pdf_buffer = generate_certificate_pdf(certificate)
        
        # Retourner la réponse HTTP avec le PDF
        from django.http import HttpResponse
        
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificat_{certificate.certificate_number}.pdf"'
        
        return response


class CertificatePreviewView(LoginRequiredMixin, View):
    """Prévisualiser un certificat dans le navigateur"""
    def get(self, request, pk):
        certificate = get_object_or_404(Certificate, pk=pk)
        
        # Vérifier les permissions
        if certificate.student != request.user:
            if not (request.user.role == 'Admin' or certificate.course.instructor == request.user):
                raise PermissionDenied("Vous n'avez pas accès à ce certificat.")
        
        from .utils import generate_certificate_pdf
        from django.http import HttpResponse
        
        pdf_buffer = generate_certificate_pdf(certificate)
        
        # Afficher dans le navigateur au lieu de télécharger
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="certificat_{certificate.certificate_number}.pdf"'
        
        return response