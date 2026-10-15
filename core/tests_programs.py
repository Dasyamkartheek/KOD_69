from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ProgramResultForm
from .models import Program, ProgramRegistration, StudentProfile


class ProgramWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='program-admin', password='test-password')
        StudentProfile.objects.create(user=self.admin, role='admin')
        self.student = User.objects.create_user(
            username='program-student', password='test-password', email='student@example.com',
        )
        StudentProfile.objects.create(user=self.student, role='student')
        self.today = timezone.localdate()

    def create_program(self, published=True):
        return Program.objects.create(
            title='Build for Change',
            organization='CodeArena Labs',
            program_type='Competition',
            description='Build a useful project.',
            registration_deadline=self.today + timedelta(days=3),
            start_date=self.today + timedelta(days=4),
            end_date=self.today + timedelta(days=5),
            delivery_mode='Online',
            published=published,
            created_by=self.admin,
        )

    def test_admin_can_create_program_and_student_can_register(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_create_program'))
        self.assertContains(response, 'Create a program')

        response = self.client.post(reverse('admin_create_program'), {
            'title': 'Build for Change',
            'organization': 'CodeArena Labs',
            'program_type': 'Competition',
            'description': 'Build a useful project.',
            'eligibility': 'Open to all students.',
            'registration_deadline': (self.today + timedelta(days=3)).isoformat(),
            'start_date': (self.today + timedelta(days=4)).isoformat(),
            'end_date': (self.today + timedelta(days=5)).isoformat(),
            'delivery_mode': 'Online',
            'location': '',
            'published': 'on',
        })
        self.assertRedirects(response, reverse('admin_programs'))
        program = Program.objects.get(title='Build for Change')
        self.assertTrue(program.published)
        self.assertEqual(program.created_by, self.admin)

        self.client.force_login(self.student)
        response = self.client.get(reverse('program_list'))
        self.assertContains(response, 'Build for Change')
        registration_url = reverse('program_register', args=[program.id])
        self.client.post(registration_url)
        self.client.post(registration_url)
        self.assertEqual(ProgramRegistration.objects.filter(program=program, student=self.student).count(), 1)

    def test_result_is_private_until_admin_publishes_it(self):
        program = self.create_program()
        registration = ProgramRegistration.objects.create(program=program, student=self.student)

        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_program_results', args=[program.id]))
        self.assertContains(response, self.student.username)
        result_url = reverse('admin_update_program_result', args=[registration.id])
        result_fields = f'registration-{registration.id}-'
        self.client.post(result_url, {
            f'{result_fields}result_status': 'Selected',
            f'{result_fields}score': '91.50',
            f'{result_fields}feedback': 'Excellent project.',
        })

        self.client.force_login(self.student)
        response = self.client.get(reverse('program_list'))
        self.assertNotContains(response, '91.50')
        self.assertNotContains(response, 'Excellent project.')

        self.client.force_login(self.admin)
        self.client.post(result_url, {
            f'{result_fields}result_status': 'Selected',
            f'{result_fields}score': '91.50',
            f'{result_fields}feedback': 'Excellent project.',
            f'{result_fields}result_published': 'on',
        })
        self.client.force_login(self.student)
        response = self.client.get(reverse('program_list'))
        self.assertContains(response, 'Selected')
        self.assertContains(response, '91.50')
        self.assertContains(response, 'Excellent project.')

    def test_students_cannot_manage_programs_or_register_for_drafts(self):
        draft = self.create_program(published=False)
        self.client.force_login(self.student)

        self.assertEqual(self.client.get(reverse('admin_programs')).status_code, 403)
        self.assertEqual(self.client.get(reverse('admin_create_program')).status_code, 403)
        response = self.client.get(reverse('program_list'))
        self.assertNotContains(response, draft.title)
        response = self.client.post(reverse('program_register', args=[draft.id]))
        self.assertEqual(response.status_code, 404)

    def test_admin_program_navigation_and_negative_score_validation(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('program_list'))
        self.assertRedirects(response, reverse('admin_programs'))

        registration = ProgramRegistration.objects.create(
            program=self.create_program(), student=self.student,
        )
        prefix = f'registration-{registration.id}-'
        form = ProgramResultForm({
            f'{prefix}result_status': 'Selected',
            f'{prefix}score': '-1',
            f'{prefix}feedback': '',
        }, instance=registration, prefix=f'registration-{registration.id}')
        self.assertFalse(form.is_valid())
        self.assertIn('score', form.errors)