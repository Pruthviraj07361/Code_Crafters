import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AdminProfile, StudentProfile


class AccountsTests(TestCase):
	def test_registration_logs_user_in(self):
		response = self.client.post(
			'/accounts/register/',
			{
				'username': 'newuser',
				'password1': 'A-secure-password-123',
				'password2': 'A-secure-password-123',
			},
		)

		self.assertRedirects(response, '/accounts/profile/')
		self.assertTrue(response.wsgi_request.user.is_authenticated)
		self.assertTrue(get_user_model().objects.filter(username='newuser').exists())

	def test_login_and_logout(self):
		user = get_user_model().objects.create_user(
			username='existing',
			password='A-secure-password-123',
		)

		response = self.client.post(
			'/accounts/login/',
			{'username': user.username, 'password': 'A-secure-password-123'},
		)
		self.assertRedirects(response, '/accounts/profile/')

		response = self.client.post('/accounts/logout/')
		self.assertRedirects(response, '/accounts/login/')

	def test_profile_requires_login(self):
		response = self.client.get('/accounts/profile/')

		self.assertRedirects(
			response,
			'/accounts/login/?next=/accounts/profile/',
		)

	def test_login_rejects_external_next_url(self):
		user = get_user_model().objects.create_user(
			username='existing',
			password='A-secure-password-123',
		)

		response = self.client.post(
			'/accounts/login/',
			{
				'username': user.username,
				'password': 'A-secure-password-123',
				'next': 'https://example.com',
			},
		)

		self.assertRedirects(response, '/accounts/profile/')


class LoginAPITests(TestCase):
    def _post(self, email, password):
        return self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': email, 'password': password}),
            content_type='application/json',
        )

    def test_approved_student_can_login(self):
        user = get_user_model().objects.create_user(
            username='student@example.com',
            email='student@example.com',
            password='A-secure-password-123',
        )
        StudentProfile.objects.create(
            user=user,
            name='Jane Student',
            division='A',
            division_roll_number='12',
            branch='Computer',
            phone='9999999999',
            enrollment_number='ENR001',
            is_approved=True,
        )

        response = self._post('student@example.com', 'A-secure-password-123')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('token', body)
        self.assertEqual(body['user']['role'], 'student')
        self.assertEqual(body['user']['name'], 'Jane Student')

    def test_unapproved_student_is_rejected(self):
        user = get_user_model().objects.create_user(
            username='pending@example.com',
            email='pending@example.com',
            password='A-secure-password-123',
        )
        StudentProfile.objects.create(
            user=user,
            name='Pending Student',
            division='A',
            division_roll_number='13',
            branch='Computer',
            phone='9999999999',
            enrollment_number='ENR002',
            is_approved=False,
        )

        response = self._post('pending@example.com', 'A-secure-password-123')

        self.assertEqual(response.status_code, 403)

    def test_admin_without_assigned_role_is_rejected(self):
        user = get_user_model().objects.create_user(
            username='staff@example.com',
            email='staff@example.com',
            password='A-secure-password-123',
        )
        AdminProfile.objects.create(
            user=user,
            name='Unassigned Staff',
            phone='9999999999',
            is_approved=True,
            staff_type='',
        )

        response = self._post('staff@example.com', 'A-secure-password-123')

        self.assertEqual(response.status_code, 403)

    def test_approved_faculty_can_login(self):
        user = get_user_model().objects.create_user(
            username='faculty@example.com',
            email='faculty@example.com',
            password='A-secure-password-123',
        )
        AdminProfile.objects.create(
            user=user,
            name='Dr. Faculty',
            phone='9999999999',
            is_approved=True,
            staff_type=AdminProfile.STAFF_FACULTY,
        )

        response = self._post('faculty@example.com', 'A-secure-password-123')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['user']['role'], 'faculty')

    def test_wrong_password_is_rejected(self):
        get_user_model().objects.create_user(
            username='student2@example.com',
            email='student2@example.com',
            password='A-secure-password-123',
        )

        response = self._post('student2@example.com', 'wrong-password')

        self.assertEqual(response.status_code, 401)


class ApprovalAPITests(TestCase):
    def _make_faculty(self):
        user = get_user_model().objects.create_user(
            username='faculty2@example.com', email='faculty2@example.com',
            password='A-secure-password-123',
        )
        AdminProfile.objects.create(
            user=user, name='Faculty Two', phone='1', is_approved=True,
            staff_type=AdminProfile.STAFF_FACULTY,
        )
        return user

    def _make_superuser(self):
        user = get_user_model().objects.create_user(
            username='super@example.com', email='super@example.com',
            password='A-secure-password-123',
        )
        AdminProfile.objects.create(
            user=user, name='Super One', phone='1', is_approved=True,
            staff_type=AdminProfile.STAFF_SUPERUSER,
        )
        return user

    def _make_pending_student(self):
        user = get_user_model().objects.create_user(
            username='pendingstu@example.com', email='pendingstu@example.com',
            password='A-secure-password-123',
        )
        return StudentProfile.objects.create(
            user=user, name='Pending Stu', division='A', division_roll_number='1',
            branch='CS', phone='1', enrollment_number='ENR100', is_approved=False,
        )

    def _make_pending_staff(self):
        user = get_user_model().objects.create_user(
            username='pendingstaff@example.com', email='pendingstaff@example.com',
            password='A-secure-password-123',
        )
        return AdminProfile.objects.create(
            user=user, name='Pending Staff', phone='1', is_approved=False, staff_type='',
        )

    def _token_header(self, user):
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        return {'HTTP_AUTHORIZATION': f'Bearer {token.key}'}

    def test_non_faculty_cannot_list_pending_students(self):
        student_profile = self._make_pending_student()
        response = self.client.get(
            '/api/faculty/pending-students',
            **self._token_header(student_profile.user),
        )
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_approve_pending_student(self):
        superuser = self._make_superuser()
        pending = self._make_pending_student()

        response = self.client.post(
            f'/api/faculty/students/{pending.pk}/approve',
            data=json.dumps({'approved': True}),
            content_type='application/json',
            **self._token_header(superuser),
        )

        self.assertEqual(response.status_code, 200)
        pending.refresh_from_db()
        self.assertTrue(pending.is_approved)

    def test_admin_registration_creates_pending_staff_with_requested_role(self):
        response = self.client.post(
            '/api/auth/admin/register',
            data=json.dumps({
                'name': 'New Faculty',
                'email': 'newfaculty@example.com',
                'phone': '5551234',
                'password': 'A-secure-password-123',
                'requested_role': 'faculty',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        profile = AdminProfile.objects.get(user__email='newfaculty@example.com')
        self.assertEqual(profile.staff_type, AdminProfile.STAFF_FACULTY)
        self.assertFalse(profile.is_approved)

        superuser = self._make_superuser()
        pending_response = self.client.get(
            '/api/superuser/pending-staff',
            **self._token_header(superuser),
        )

        self.assertEqual(pending_response.status_code, 200)
        self.assertEqual(pending_response.json()[0]['id'], profile.id)

    def test_admin_staff_registration_accepts_unassigned_role(self):
        response = self.client.post(
            '/api/auth/admin/register',
            data=json.dumps({
                'name': 'New Staff Applicant',
                'email': 'newstaff@example.com',
                'phone': '5559876',
                'password': 'A-secure-password-123',
                'requested_role': '',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        profile = AdminProfile.objects.get(user__email='newstaff@example.com')
        self.assertEqual(profile.staff_type, '')
        self.assertFalse(profile.is_approved)

    def test_faculty_can_approve_student(self):
        faculty = self._make_faculty()
        pending = self._make_pending_student()

        response = self.client.post(
            f'/api/faculty/students/{pending.pk}/approve',
            data=json.dumps({'approved': True}),
            content_type='application/json',
            **self._token_header(faculty),
        )

        self.assertEqual(response.status_code, 200)
        pending.refresh_from_db()
        self.assertTrue(pending.is_approved)

    def test_faculty_can_reject_student(self):
        faculty = self._make_faculty()
        pending = self._make_pending_student()

        response = self.client.post(
            f'/api/faculty/students/{pending.pk}/approve',
            data=json.dumps({'approved': False}),
            content_type='application/json',
            **self._token_header(faculty),
        )

        self.assertEqual(response.status_code, 200)
        pending.refresh_from_db()
        self.assertFalse(pending.is_approved)
        self.assertFalse(pending.user.is_active)

    def test_superuser_can_assign_staff_role(self):
        superuser = self._make_superuser()
        pending = self._make_pending_staff()

        response = self.client.post(
            f'/api/superuser/staff/{pending.pk}/assign-role',
            data=json.dumps({'staff_type': 'supervisor', 'approved': True}),
            content_type='application/json',
            **self._token_header(superuser),
        )

        self.assertEqual(response.status_code, 200)
        pending.refresh_from_db()
        self.assertEqual(pending.staff_type, 'supervisor')
        self.assertTrue(pending.is_approved)

    def test_faculty_cannot_assign_staff_role(self):
        faculty = self._make_faculty()
        pending = self._make_pending_staff()

        response = self.client.post(
            f'/api/superuser/staff/{pending.pk}/assign-role',
            data=json.dumps({'staff_type': 'supervisor', 'approved': True}),
            content_type='application/json',
            **self._token_header(faculty),
        )

        self.assertEqual(response.status_code, 403)
