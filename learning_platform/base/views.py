from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View,TemplateView
from django.urls import reverse_lazy
from .models import *
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
    fields = ['title', 'description', 'estimated_duration', 'level', 'start_date', 'end_date', 'image'] 
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
    fields = ['title', 'description', 'estimated_duration', 'level', 'start_date', 'end_date', 'image']
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
        modules = course.modules.all()
        
        selected_module_id = request.GET.get('module_id')
        selected_module = None
        resources = []
        evaluations = []

        if selected_module_id:
            selected_module = get_object_or_404(Module, pk=selected_module_id, course=course)
        elif modules:
            selected_module = modules[0]  # par défaut le premier module

        if selected_module:
            resources = selected_module.resources.all()  # suppose que tu as une relation vers les ressources
            evaluations = selected_module.evaluations.all()

        return render(request, 'modules/module_list.html', {
            'course': course,
            'modules': modules,
            'selected_module': selected_module,
            'resources': resources,
            'evaluations':evaluations,
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
        return super().form_valid(form)

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
    fields = ['title', 'evaluation_type', 'deadline']
    template_name = 'evaluations/evaluation_form.html'

    def form_valid(self, form):
        module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        form.instance.module = module
        return super().form_valid(form)

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
        # Récupérer manuellement l'objet sans utiliser self.get_object()
        evaluation = get_object_or_404(Resource, pk=self.kwargs['pk'])
        course = evaluation.module.course

        if request.user.role == 'Admin' or course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("You can't create this evaluation.")



class EvaluationUpdateView(AdminOrInstructorRequiredMixin, UpdateView):
    model = Evaluation
    fields = ['title', 'evaluation_type', 'deadline']
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
            messages.error(request, "Only students can enroll in courses.")
            return redirect('course-detail', pk=pk)

        # Vérifie si déjà inscrit
        already_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        if already_enrolled:
            messages.info(request, "You are already enrolled in this course.")
        else:
            Enrollment.objects.create(student=request.user, course=course)
            messages.success(request, "Successfully enrolled in the course!")

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
        else:
            messages.info(request, "You are not enrolled in this course.")

        return redirect('course-detail', pk=pk)
    



class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']  # ne modifie pas le rôle ici

class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'students/dashboard.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        form = UserUpdateForm(instance=user)

        # Cours où il est inscrit
        enrolled_courses = Course.objects.filter(enrollments__student=user)

        # Cours non inscrits pour suggestions
        suggested_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))[:6]

        # Certificats (adapter selon ton modèle)
        certificates = Certificate.objects.filter(student=user)

        context = {
            'form': form,
            'enrolled_courses': enrolled_courses,
            'suggested_courses': suggested_courses,
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
        certificates = Certificate.objects.filter(student=user)

        context = {
            'form': form,
            'enrolled_courses': enrolled_courses,
            'suggested_courses': suggested_courses,
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