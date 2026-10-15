from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CodeSubmission, ProgrammingChallenge, StudentProfile


class AdminSignupTests(TestCase):
    @override_settings(ADMIN_SIGNUP_CODE='', DEBUG=True)
    def test_first_admin_can_bootstrap_locally_once(self):
        response = self.client.get(reverse('admin_signup'))
        self.assertContains(response, 'one-time setup')

        response = self.client.post(reverse('admin_signup'), {
            'username': 'first-admin',
            'first_name': 'First',
            'last_name': 'Admin',
            'email': 'first-admin@example.com',
            'password1': 'F!y3r8#Gz2vP9$LmQ4',
            'password2': 'F!y3r8#Gz2vP9$LmQ4',
        })
        self.assertRedirects(response, reverse('dashboard'))
        first_admin = User.objects.get(username='first-admin')
        self.assertTrue(StudentProfile.objects.filter(user=first_admin, role='admin').exists())

        self.client.logout()
        response = self.client.get(reverse('admin_signup'))
        self.assertContains(response, 'Admin signup is currently disabled')

    @override_settings(ADMIN_SIGNUP_CODE='', DEBUG=True)
    def test_first_admin_bootstrap_is_blocked_for_remote_requests(self):
        response = self.client.get(reverse('admin_signup'), REMOTE_ADDR='192.0.2.10')

        self.assertContains(response, 'Admin signup is currently disabled')

    @override_settings(ADMIN_SIGNUP_CODE='correct-invite-code')
    def test_valid_invite_creates_admin_account(self):
        response = self.client.post(reverse('admin_signup'), {
            'username': 'new-admin',
            'first_name': 'Site',
            'last_name': 'Admin',
            'email': 'admin@example.com',
            'password1': 'F!y3r8#Gz2vP9$LmQ4',
            'password2': 'F!y3r8#Gz2vP9$LmQ4',
            'invite_code': 'correct-invite-code',
        })

        self.assertRedirects(response, reverse('dashboard'))
        admin_user = User.objects.get(username='new-admin')
        self.assertTrue(StudentProfile.objects.filter(user=admin_user, role='admin').exists())
        self.assertFalse(admin_user.is_staff)
        self.assertEqual(int(self.client.session['_auth_user_id']), admin_user.id)

    @override_settings(ADMIN_SIGNUP_CODE='correct-invite-code')
    def test_invalid_invite_does_not_create_admin_account(self):
        response = self.client.post(reverse('admin_signup'), {
            'username': 'not-admin',
            'first_name': '',
            'last_name': '',
            'email': 'not-admin@example.com',
            'password1': 'F!y3r8#Gz2vP9$LmQ4',
            'password2': 'F!y3r8#Gz2vP9$LmQ4',
            'invite_code': 'wrong-code',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'invitation code is invalid')
        self.assertFalse(User.objects.filter(username='not-admin').exists())


class AdminCreateChallengeTests(TestCase):
    def test_admin_profile_can_publish_challenge_for_students(self):
        admin_user = User.objects.create_user(username='content-admin', password='test-password')
        StudentProfile.objects.create(user=admin_user, role='admin')
        self.client.force_login(admin_user)
        response = self.client.get(reverse('admin_create_challenge'))
        self.assertContains(response, 'Add programming challenge')

        response = self.client.post(reverse('admin_create_challenge'), {
            'title': 'Loops',
            'description': 'Practice loops.',
            'topic': 'Python Basics',
            'difficulty': 'Easy',
            'sample_input': '3',
            'sample_output': '123',
            'marks': 10,
            'published': 'on',
            'test_cases-TOTAL_FORMS': '1',
            'test_cases-INITIAL_FORMS': '0',
            'test_cases-MIN_NUM_FORMS': '0',
            'test_cases-MAX_NUM_FORMS': '1000',
            'test_cases-0-name': 'Example',
            'test_cases-0-input_data': '3',
            'test_cases-0-expected_output': '123',
            'test_cases-0-order': '0',
        })

        self.assertRedirects(response, reverse('dashboard'))
        challenge = ProgrammingChallenge.objects.get(title='Loops')
        self.assertTrue(challenge.published)
        self.assertEqual(challenge.created_by, admin_user)
        self.assertEqual(challenge.test_cases.count(), 1)

        student = User.objects.create_user(username='learner', password='test-password')
        StudentProfile.objects.create(user=student, role='student')
        self.client.force_login(student)
        response = self.client.get(reverse('challenge_list'))
        self.assertContains(response, 'Loops')
        response = self.client.get(reverse('submit_code', args=[challenge.id]))
        self.assertContains(response, 'Run test cases')
        self.assertContains(response, 'Example')

    def test_admin_login_accepts_admin_and_rejects_student(self):
        admin_user = User.objects.create_user(username='staff-admin', password='test-password')
        StudentProfile.objects.create(user=admin_user, role='admin')
        response = self.client.post(reverse('admin_login'), {
            'username': admin_user.username,
            'password': 'test-password',
        })
        self.assertRedirects(response, reverse('dashboard'))

        self.client.logout()
        student = User.objects.create_user(username='learner', password='test-password')
        StudentProfile.objects.create(user=student, role='student')
        response = self.client.post(reverse('admin_login'), {
            'username': student.username,
            'password': 'test-password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'does not have admin access')

    def test_admin_can_edit_test_cases_and_student_can_submit_from_ide(self):
        admin_user = User.objects.create_user(username='content-admin', password='test-password')
        StudentProfile.objects.create(user=admin_user, role='admin')
        challenge = ProgrammingChallenge.objects.create(
            title='Loops', description='Practice loops.', published=True,
        )
        test_case = challenge.test_cases.create(name='Example', input_data='3', expected_output='123')
        self.client.force_login(admin_user)
        response = self.client.post(reverse('admin_edit_challenge', args=[challenge.id]), {
            'title': 'Loop practice',
            'description': 'Practice loops with a counter.',
            'topic': 'Python Basics',
            'difficulty': 'Easy',
            'sample_input': '',
            'sample_output': '',
            'marks': '10',
            'published': 'on',
            'test_cases-TOTAL_FORMS': '1',
            'test_cases-INITIAL_FORMS': '1',
            'test_cases-MIN_NUM_FORMS': '0',
            'test_cases-MAX_NUM_FORMS': '1000',
            'test_cases-0-id': str(test_case.id),
            'test_cases-0-name': 'Three counts',
            'test_cases-0-input_data': '3',
            'test_cases-0-expected_output': '123',
            'test_cases-0-order': '0',
        })
        self.assertRedirects(response, reverse('admin_challenges'))
        test_case.refresh_from_db()
        self.assertEqual(test_case.name, 'Three counts')

        student = User.objects.create_user(username='learner', password='test-password')
        StudentProfile.objects.create(user=student, role='student')
        self.client.force_login(student)
        response = self.client.post(reverse('submit_code', args=[challenge.id]), {
            'source_code': 'print(123)',
        })
        self.assertRedirects(response, reverse('challenge_list'))
        self.assertEqual(CodeSubmission.objects.get(student=student).source_code, 'print(123)')

    def test_student_cannot_create_challenge(self):
        student = User.objects.create_user(username='learner', password='test-password')
        StudentProfile.objects.create(user=student, role='student')
        self.client.force_login(student)

        response = self.client.get(reverse('admin_create_challenge'))

        self.assertEqual(response.status_code, 403)