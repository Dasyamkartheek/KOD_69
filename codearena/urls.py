from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from core import views
from core.forms import AdminAuthenticationForm

urlpatterns = [
    path('manage/challenges/add/', views.admin_create_challenge, name='admin_create_challenge'),
    path('manage/challenges/', views.admin_challenges, name='admin_challenges'),
    path('manage/challenges/<int:challenge_id>/edit/', views.admin_edit_challenge, name='admin_edit_challenge'),
    path('manage/programs/', views.admin_programs, name='admin_programs'),
    path('manage/programs/add/', views.admin_create_program, name='admin_create_program'),
    path('manage/programs/<int:program_id>/results/', views.admin_program_results, name='admin_program_results'),
    path('manage/program-registrations/<int:registration_id>/result/', views.admin_update_program_result, name='admin_update_program_result'),
    path('admin-login/', auth_views.LoginView.as_view(
        template_name='registration/admin_login.html',
        authentication_form=AdminAuthenticationForm,
    ), name='admin_login'),
    path('admin-signup/', views.admin_signup, name='admin_signup'),
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quizzes/<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),
    path('practice/', views.challenge_list, name='challenge_list'),
    path('practice/<int:challenge_id>/', views.submit_code, name='submit_code'),
    path('programs/', views.program_list, name='program_list'),
    path('programs/<int:program_id>/register/', views.program_register, name='program_register'),
]
