from django.urls import path, include
from .views import *
from django.contrib.auth.views import LoginView, LogoutView




urlpatterns = [

    # =====================================================
    # COURSES
    # =====================================================
    path('courses/', CourseListView.as_view(), name='course-list'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('courses/create/', CourseCreateView.as_view(), name='course-create'),
    path('courses/update/<int:pk>/', CourseUpdateView.as_view(), name='course-update'),
    path('courses/delete/<int:pk>/', CourseDeleteView.as_view(), name='course-delete'),


    # =====================================================
    # MODULES
    # =====================================================
    path('modules/course/<int:course_id>/', ModuleListView.as_view(), name='module-list-by-course'),
    path('modules/create/<int:course_id>/', ModuleCreateView.as_view(), name='module-create'),
    path('modules/update/<int:pk>/', ModuleUpdateView.as_view(), name='module-update'),
    path('modules/delete/<int:pk>/', ModuleDeleteView.as_view(), name='module-delete'),


    # =====================================================
    # RESOURCES
    # =====================================================
    path('module/<int:module_id>/resources/add/', ResourceCreateView.as_view(), name='resource-add'),
    path('resources/<int:pk>/edit/', ResourceUpdateView.as_view(), name='resource-edit'),
    path('resources/<int:pk>/delete/', ResourceDeleteView.as_view(), name='resource-delete'),
    path('resources/<int:pk>/view/', MarkResourceViewedView.as_view(), name='resource-view'),


    # =====================================================
    # EVALUATIONS
    # =====================================================
    path('module/<int:module_id>/evaluation/add/', EvaluationCreateView.as_view(), name='evaluation-add'),
    path('evaluation/<int:pk>/edit/', EvaluationUpdateView.as_view(), name='evaluation-edit'),
    path('evaluation/<int:pk>/delete/', EvaluationDeleteView.as_view(), name='evaluation-delete'),


    # =====================================================
    # QUESTIONS (CRUD pour Quiz)
    # =====================================================
    path('evaluation/<int:evaluation_id>/questions/', QuestionListView.as_view(), name='question-list'),
    path('evaluation/<int:evaluation_id>/questions/add/', QuestionCreateView.as_view(), name='question-create'),
    path('questions/<int:pk>/edit/', QuestionUpdateView.as_view(), name='question-edit'),
    path('questions/<int:pk>/delete/', QuestionDeleteView.as_view(), name='question-delete'),


    # =====================================================
    # QUIZ (Passer un Quiz)
    # =====================================================
    path('evaluation/<int:pk>/take/', QuizTakeView.as_view(), name='quiz-take'),
    path('evaluation/<int:pk>/submit/', QuizSubmitView.as_view(), name='quiz-submit'),
    path('submission/<int:pk>/results/', QuizResultView.as_view(), name='quiz-results'),


    # =====================================================
    # ASSIGNMENTS (Soumettre un Devoir)
    # =====================================================
    path('evaluation/<int:pk>/submit-assignment/', AssignmentSubmitView.as_view(), name='assignment-submit'),
    path('evaluation/<int:evaluation_id>/submissions/', SubmissionListView.as_view(), name='submission-list'),
    path('submission/<int:pk>/grade/', SubmissionGradeView.as_view(), name='submission-grade'),


    # =====================================================
    # AUTHENTICATION
    # =====================================================
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),


    # =====================================================
    # ENROLLMENT (Inscription aux cours)
    # =====================================================
    path('courses/<int:pk>/enroll/', EnrollView.as_view(), name='enroll'),
    path('courses/<int:pk>/unenroll/', UnenrollView.as_view(), name='unenroll'),


    # =====================================================
    # DASHBOARDS
    # =====================================================
    path('student/dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher-dashboard'),


    # =====================================================
    # NOTIFICATIONS
    # =====================================================
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),


    # =====================================================
    # HOME
    # =====================================================
    path('', TemplateView.as_view(template_name='home.html'), name='home'),


    # =====================================================
    # CERTIFICATES
    # =====================================================
    path('certificates/', CertificateListView.as_view(), name='certificate-list'),
    path('certificates/<int:pk>/download/', CertificateDownloadView.as_view(), name='certificate-download'),
    path('certificates/<int:pk>/preview/', CertificatePreviewView.as_view(), name='certificate-preview'),

]

