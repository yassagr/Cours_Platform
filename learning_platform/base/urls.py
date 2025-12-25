from django.urls import path, include
from .views import *
from django.contrib.auth.views import LoginView,LogoutView




urlpatterns = [

# courses/urls.py
    path('courses/', CourseListView.as_view(), name='course-list'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('courses/create/', CourseCreateView.as_view(), name='course-create'),
    path('courses/update/<int:pk>', CourseUpdateView.as_view(), name='course-update'),
    path('courses/delete/<int:pk>', CourseDeleteView.as_view(), name='course-delete'),


# modules/urls.py
    path('modules/course/<int:course_id>/', ModuleListView.as_view(), name='module-list-by-course'),
    path('modules/create/<int:course_id>/', ModuleCreateView.as_view(), name='module-create'),
    path('modules/update/<int:pk>/', ModuleUpdateView.as_view(), name='module-update'),
    path('modules/delete/<int:pk>/', ModuleDeleteView.as_view(), name='module-delete'),


# resources/urls.py
    path('module/<int:module_id>/resources/add/', ResourceCreateView.as_view(), name='resource-add'),
    path('resources/<int:pk>/edit/', ResourceUpdateView.as_view(), name='resource-edit'),
    path('resources/<int:pk>/delete/', ResourceDeleteView.as_view(), name='resource-delete'),


# Evaluations/urls.py
    path('module/<int:module_id>/evaluation/add/', EvaluationCreateView.as_view(), name='evaluation-add'),
    path('evaluation/<int:pk>/edit/', EvaluationUpdateView.as_view(), name='evaluation-edit'),
    path('evaluation/<int:pk>/delete/', EvaluationDeleteView.as_view(), name='evaluation-delete'),


# signup/urls.py
    path('signup/', SignUpView.as_view(), name='signup'),
# login/urls.py
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
# logout/urls.py
    path('logout/', LogoutView.as_view(), name='logout'),


# enroll/urls.py
    path('courses/<int:pk>/enroll/', EnrollView.as_view(), name='enroll'),
    path('courses/<int:pk>/unenroll/', UnenrollView.as_view(), name='unenroll'),



# dashboard/urls.py
    path('student/dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher-dashboard'),


# home/urls.py
    path('', TemplateView.as_view(template_name='home.html'), name='home'),


]
