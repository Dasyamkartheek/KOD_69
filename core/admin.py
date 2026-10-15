from django.contrib import admin
from .models import (
    StudentProfile, Quiz, Question, QuizAttempt, ProgrammingChallenge,
    ProgrammingTestCase, CodeSubmission, Program, ProgramRegistration,
)

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'published', 'duration_minutes', 'created_at')
    list_filter = ('published', 'topic')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]

class ProgrammingTestCaseInline(admin.TabularInline):
    model = ProgrammingTestCase
    extra = 1

@admin.register(ProgrammingChallenge)
class ProgrammingChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'difficulty', 'marks', 'published')
    list_filter = ('published', 'difficulty', 'topic')
    search_fields = ('title', 'description')
    inlines = [ProgrammingTestCaseInline]

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'registration_number', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'registration_number')

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'total_marks', 'submitted_at')
    readonly_fields = ('student', 'quiz', 'score', 'total_marks', 'answers', 'submitted_at')

@admin.register(CodeSubmission)
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'challenge', 'status', 'submitted_at')
    readonly_fields = ('student', 'challenge', 'source_code', 'submitted_at', 'status')

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'program_type', 'start_date', 'published')
    list_filter = ('published', 'program_type', 'delivery_mode')
    search_fields = ('title', 'organization', 'description')

@admin.register(ProgramRegistration)
class ProgramRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'program', 'result_status', 'score', 'result_published', 'registered_at')
    list_filter = ('program', 'result_status', 'result_published')
    search_fields = ('student__username', 'student__email', 'program__title')
