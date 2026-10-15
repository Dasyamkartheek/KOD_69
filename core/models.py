from django.conf import settings
from django.db import models

class StudentProfile(models.Model):
    ROLE_CHOICES = [('student', 'Student'), ('admin', 'Admin')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    registration_number = models.CharField(max_length=40, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return f'{self.user.username} ({self.role})'

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    topic = models.CharField(max_length=100, default='Python Basics')
    duration_minutes = models.PositiveIntegerField(default=15)
    published = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def total_marks(self):
        return sum(q.points for q in self.questions.all())

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])
    explanation = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.text[:80]

class QuizAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    answers = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

class ProgrammingChallenge(models.Model):
    DIFFICULTY_CHOICES = [('Easy','Easy'),('Medium','Medium'),('Hard','Hard')]
    title = models.CharField(max_length=200)
    description = models.TextField()
    topic = models.CharField(max_length=100, default='Python Basics')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='Easy')
    sample_input = models.TextField(blank=True)
    sample_output = models.TextField(blank=True)
    marks = models.PositiveIntegerField(default=10)
    published = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['difficulty', 'title']

    def __str__(self):
        return self.title

class ProgrammingTestCase(models.Model):
    challenge = models.ForeignKey(
        ProgrammingChallenge, on_delete=models.CASCADE, related_name='test_cases',
    )
    name = models.CharField(max_length=100, default='Test case')
    input_data = models.TextField(blank=True)
    expected_output = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.challenge.title}: {self.name}'

class CodeSubmission(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    challenge = models.ForeignKey(ProgrammingChallenge, on_delete=models.CASCADE)
    source_code = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default='Submitted for review')

    class Meta:
        ordering = ['-submitted_at']

class Program(models.Model):
    PROGRAM_TYPES = [
        ('Competition', 'Competition'),
        ('Hackathon', 'Hackathon'),
        ('Workshop', 'Workshop'),
        ('Internship', 'Internship'),
        ('Scholarship', 'Scholarship'),
    ]
    DELIVERY_MODES = [
        ('Online', 'Online'),
        ('Offline', 'Offline'),
        ('Hybrid', 'Hybrid'),
    ]

    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=120, default='CodeArena')
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPES, default='Competition')
    description = models.TextField()
    eligibility = models.TextField(blank=True)
    registration_deadline = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField()
    delivery_mode = models.CharField(max_length=10, choices=DELIVERY_MODES, default='Online')
    location = models.CharField(max_length=200, blank=True)
    published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_programs',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date', 'title']

    def __str__(self):
        return self.title

class ProgramRegistration(models.Model):
    RESULT_STATUSES = [
        ('Pending', 'Pending'),
        ('Participated', 'Participated'),
        ('Shortlisted', 'Shortlisted'),
        ('Selected', 'Selected'),
        ('Not selected', 'Not selected'),
    ]

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='registrations')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='program_registrations',
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    result_status = models.CharField(max_length=20, choices=RESULT_STATUSES, default='Pending')
    score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    result_published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-registered_at']
        constraints = [
            models.UniqueConstraint(fields=['program', 'student'], name='unique_program_student_registration'),
        ]

    def __str__(self):
        return f'{self.student.username} - {self.program.title}'
