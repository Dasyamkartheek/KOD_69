from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import (
    AdminSignupForm, ProgramForm, ProgramResultForm, ProgrammingChallengeForm,
    ProgrammingTestCaseFormSet, RegistrationForm,
)
from .models import (
    StudentProfile, Quiz, QuizAttempt, ProgrammingChallenge, CodeSubmission,
    Program, ProgramRegistration,
)


def is_admin_user(user):
    return user.is_staff or user.is_superuser or StudentProfile.objects.filter(user=user, role='admin').exists()


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your student account has been created.')
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def admin_signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    has_admin_account = User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True) | Q(studentprofile__role='admin'),
    ).exists()
    is_local_request = request.META.get('REMOTE_ADDR') in {'127.0.0.1', '::1'}
    bootstrap_allowed = (
        settings.DEBUG and is_local_request and not has_admin_account
        and not settings.ADMIN_SIGNUP_CODE
    )
    form = AdminSignupForm(request.POST or None, allow_bootstrap=bootstrap_allowed)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Admin account created. Welcome to the admin workspace.')
        return redirect('dashboard')
    return render(request, 'registration/admin_signup.html', {
        'form': form,
        'signup_enabled': bool(settings.ADMIN_SIGNUP_CODE) or bootstrap_allowed,
        'bootstrap_allowed': bootstrap_allowed,
    })

@login_required
def dashboard(request):
    if is_admin_user(request.user):
        return render(request, 'core/admin_dashboard.html', {
            'student_count': User.objects.filter(is_staff=False, is_superuser=False).count(),
            'quiz_count': Quiz.objects.count(),
            'challenge_count': ProgrammingChallenge.objects.count(),
            'attempt_count': QuizAttempt.objects.count(),
            'recent_attempts': QuizAttempt.objects.select_related('student', 'quiz')[:8],
            'program_count': Program.objects.count(),
            'program_registration_count': ProgramRegistration.objects.count(),
        })
    attempts = QuizAttempt.objects.filter(student=request.user).select_related('quiz')
    submissions = CodeSubmission.objects.filter(student=request.user).select_related('challenge')
    program_registrations = ProgramRegistration.objects.filter(
        student=request.user, program__published=True,
    ).select_related('program')
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    return render(request, 'core/student_dashboard.html', {
        'profile': profile,
        'quizzes': Quiz.objects.filter(published=True),
        'challenges': ProgrammingChallenge.objects.filter(published=True),
        'attempts': attempts[:5],
        'submissions': submissions[:5],
        'attempt_count': attempts.count(),
        'submission_count': submissions.count(),
        'program_registrations': program_registrations[:5],
        'program_count': Program.objects.filter(published=True).count(),
    })

@login_required
def quiz_list(request):
    if is_admin_user(request.user):
        return redirect('/admin/core/quiz/')
    return render(request, 'core/quiz_list.html', {'quizzes': Quiz.objects.filter(published=True)})

@login_required
def take_quiz(request, quiz_id):
    if is_admin_user(request.user):
        return HttpResponseForbidden('Admin accounts cannot participate in student quizzes.')
    quiz = get_object_or_404(Quiz, pk=quiz_id, published=True)
    questions = list(quiz.questions.all())
    if not questions:
        messages.info(request, 'This quiz does not have any questions yet.')
        return redirect('quiz_list')
    if request.method == 'POST':
        answers = {}
        score = 0
        for question in questions:
            answer = request.POST.get(f'q_{question.id}', '')
            if answer in {'A', 'B', 'C', 'D'}:
                answers[str(question.id)] = answer
                if answer == question.correct_option:
                    score += question.points
        attempt = QuizAttempt.objects.create(
            student=request.user, quiz=quiz, score=score,
            total_marks=sum(q.points for q in questions), answers=answers
        )
        return redirect('quiz_result', quiz_id=attempt.id)
    return render(request, 'core/take_quiz.html', {'quiz': quiz, 'questions': questions})

@login_required
def quiz_result(request, quiz_id):
    attempt = get_object_or_404(QuizAttempt.objects.select_related('quiz'), pk=quiz_id)
    if attempt.student_id != request.user.id and not is_admin_user(request.user):
        return HttpResponseForbidden('You cannot view another student’s result.')
    question_results = []
    for question in attempt.quiz.questions.all():
        selected = attempt.answers.get(str(question.id), '')
        question_results.append({
            'question': question,
            'selected': selected,
            'correct': selected == question.correct_option,
            'selected_text': getattr(question, {'A':'option_a','B':'option_b','C':'option_c','D':'option_d'}.get(selected, 'option_a')) if selected else 'Not answered',
            'correct_text': getattr(question, {'A':'option_a','B':'option_b','C':'option_c','D':'option_d'}[question.correct_option]),
        })
    return render(request, 'core/quiz_result.html', {'attempt': attempt, 'question_results': question_results})

@login_required
def challenge_list(request):
    if is_admin_user(request.user):
        return redirect('admin_challenges')
    return render(request, 'core/challenge_list.html', {'challenges': ProgrammingChallenge.objects.filter(published=True)})

@login_required
def admin_create_challenge(request):
    return _admin_challenge_form(request)

@login_required
def admin_edit_challenge(request, challenge_id):
    challenge = get_object_or_404(ProgrammingChallenge, pk=challenge_id)
    return _admin_challenge_form(request, challenge, is_edit=True)

def _admin_challenge_form(request, challenge=None, is_edit=False):
    if not is_admin_user(request.user):
        return HttpResponseForbidden('Only admins can create programming challenges.')
    form = ProgrammingChallengeForm(request.POST or None, instance=challenge)
    test_case_formset = ProgrammingTestCaseFormSet(
        request.POST or None, instance=form.instance,
    )
    if request.method == 'POST':
        if form.is_valid() and test_case_formset.is_valid():
            challenge = form.save(commit=False)
            if not is_edit:
                challenge.created_by = request.user
            challenge.save()
            test_case_formset.instance = challenge
            test_case_formset.save()
            messages.success(request, 'Challenge updated successfully.' if is_edit else 'Challenge created successfully.')
            return redirect('admin_challenges' if is_edit else 'dashboard')
    return render(request, 'core/challenge_form.html', {
        'form': form,
        'test_case_formset': test_case_formset,
        'challenge': challenge,
    })

@login_required
def admin_challenges(request):
    if not is_admin_user(request.user):
        return HttpResponseForbidden('Only admins can manage programming challenges.')
    challenges = ProgrammingChallenge.objects.annotate(test_case_count=Count('test_cases'))
    return render(request, 'core/admin_challenges.html', {'challenges': challenges})

@login_required
def program_list(request):
    if is_admin_user(request.user):
        return redirect('admin_programs')
    programs = Program.objects.filter(published=True)
    query = request.GET.get('q', '').strip()
    program_type = request.GET.get('type', '')
    if query:
        programs = programs.filter(Q(title__icontains=query) | Q(organization__icontains=query))
    if program_type:
        programs = programs.filter(program_type=program_type)
    registrations = ProgramRegistration.objects.filter(
        student=request.user, program__published=True,
    ).select_related('program')
    registrations_by_program = {item.program_id: item for item in registrations}
    program_cards = [
        {'program': program, 'registration': registrations_by_program.get(program.id)}
        for program in programs
    ]
    return render(request, 'core/program_list.html', {
        'program_cards': program_cards,
        'program_types': Program.PROGRAM_TYPES,
        'selected_type': program_type,
        'search_query': query,
        'today': timezone.localdate(),
    })

@login_required
@require_POST
def program_register(request, program_id):
    if is_admin_user(request.user):
        return HttpResponseForbidden('Admin accounts cannot register for student programs.')
    program = get_object_or_404(Program, pk=program_id, published=True)
    if program.registration_deadline < timezone.localdate():
        messages.error(request, 'Registration for this program has closed.')
        return redirect('program_list')
    _, created = ProgramRegistration.objects.get_or_create(program=program, student=request.user)
    if created:
        messages.success(request, f'You are registered for {program.title}.')
    else:
        messages.info(request, 'You are already registered for this program.')
    return redirect('program_list')

@login_required
def admin_programs(request):
    if not is_admin_user(request.user):
        return HttpResponseForbidden('Only admins can manage programs.')
    programs = Program.objects.annotate(registrant_count=Count('registrations'))
    return render(request, 'core/admin_programs.html', {'programs': programs})

@login_required
def admin_create_program(request):
    if not is_admin_user(request.user):
        return HttpResponseForbidden('Only admins can create programs.')
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save(commit=False)
            program.created_by = request.user
            program.save()
            messages.success(request, 'Program saved successfully.')
            return redirect('admin_programs')
    else:
        form = ProgramForm()
    return render(request, 'core/program_form.html', {'form': form})

@login_required
def admin_program_results(request, program_id):
    if not is_admin_user(request.user):
        return HttpResponseForbidden('Only admins can manage program results.')
    program = get_object_or_404(Program, pk=program_id)
    participants = [
        {
            'registration': registration,
            'form': ProgramResultForm(instance=registration, prefix=f'registration-{registration.id}'),
        }
        for registration in program.registrations.select_related('student')
    ]
    return render(request, 'core/admin_program_results.html', {
        'program': program,
        'participants': participants,
    })

@login_required
@require_POST
def admin_update_program_result(request, registration_id):
    if not is_admin_user(request.user):
        return HttpResponseForbidden('Only admins can update program results.')
    registration = get_object_or_404(ProgramRegistration, pk=registration_id)
    form = ProgramResultForm(
        request.POST, instance=registration, prefix=f'registration-{registration.id}',
    )
    if form.is_valid():
        form.save()
        messages.success(request, f'Result updated for {registration.student.username}.')
    else:
        messages.error(request, 'The result could not be saved. Please check the submitted values.')
    return redirect('admin_program_results', program_id=registration.program_id)

@login_required
def submit_code(request, challenge_id):
    if is_admin_user(request.user):
        return HttpResponseForbidden('Admin accounts cannot submit student practice code.')
    challenge = get_object_or_404(ProgrammingChallenge, pk=challenge_id, published=True)
    if request.method == 'POST':
        source_code = request.POST.get('source_code', '').strip()
        if not source_code:
            messages.error(request, 'Please write your Python code before submitting.')
        elif len(source_code) > 50000:
            messages.error(request, 'Your submission is too long. Please keep it under 50,000 characters.')
        else:
            CodeSubmission.objects.create(student=request.user, challenge=challenge, source_code=source_code)
            messages.success(request, 'Your code has been saved for review. It has not been executed.')
            return redirect('challenge_list')
    previous = CodeSubmission.objects.filter(student=request.user, challenge=challenge)[:5]
    return render(request, 'core/submit_code.html', {
        'challenge': challenge,
        'test_cases': list(challenge.test_cases.values('name', 'input_data', 'expected_output')),
        'previous': previous,
    })
