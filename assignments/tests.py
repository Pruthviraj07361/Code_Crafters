import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token

from accounts.models import AdminProfile, StudentProfile

from .models import Meeting, ProblemStatement


class AssignmentsTestBase(TestCase):
    def _make_admin(self, email, staff_type, name='Staff Member'):
        user = get_user_model().objects.create_user(
            username=email, email=email, password='A-secure-password-123',
        )
        AdminProfile.objects.create(
            user=user, name=name, phone='1', is_approved=True, staff_type=staff_type,
        )
        return user

    def _make_supervisor(self):
        return self._make_admin(
            'supervisor@example.com', AdminProfile.STAFF_SUPERVISOR, name='Sam Supervisor',
        )

    def _make_native_superuser(self):
        return get_user_model().objects.create_superuser(
            username='root-admin',
            email='root@example.com',
            password='A-secure-password-123',
        )

    def _make_faculty(self):
        return self._make_admin('faculty@example.com', AdminProfile.STAFF_FACULTY)

    def _make_student(self, email='student@example.com', enrollment='ENR001', approved=True):
        user = get_user_model().objects.create_user(
            username=email, email=email, password='A-secure-password-123',
        )
        StudentProfile.objects.create(
            user=user, name='Test Student', division='A', division_roll_number='1',
            branch='CS', phone='1', enrollment_number=enrollment, is_approved=approved,
        )
        return user

    def _make_problem(self, supervisor_user, title='Two Sum', **extra):
        return ProblemStatement.objects.create(
            title=title,
            description='Add two numbers.',
            sample_input='1 2\n',
            test_cases=[{'input': '1 2\n', 'expected_output': '3\n'}],
            created_by=supervisor_user.admin_profile,
            **extra,
        )

    def _token_header(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        return {'HTTP_AUTHORIZATION': f'Bearer {token.key}'}

    def _post_json(self, path, payload, user=None):
        extra = self._token_header(user) if user else {}
        return self.client.post(
            path, data=json.dumps(payload), content_type='application/json', **extra,
        )

    def _get(self, path, user=None):
        extra = self._token_header(user) if user else {}
        return self.client.get(path, **extra)


class SupervisorProblemStatementTests(AssignmentsTestBase):
    PAYLOAD = {
        'title': 'Reverse a String',
        'description': 'Read a string and print it reversed.',
        'sample_input': 'hello\n',
        'test_cases': [
            {'input': 'hello\n', 'expected_output': 'olleh\n'},
            {'input': 'world\n', 'expected_output': 'dlrow\n'},
        ],
        'week_number': 2,
    }

    def test_supervisor_can_create_problem_statement(self):
        supervisor = self._make_supervisor()

        response = self._post_json('/api/supervisor/problem-statements', self.PAYLOAD, supervisor)

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['title'], 'Reverse a String')
        self.assertEqual(body['created_by_name'], 'Sam Supervisor')
        problem = ProblemStatement.objects.get(pk=body['id'])
        self.assertEqual(problem.created_by, supervisor.admin_profile)
        self.assertEqual(problem.week_number, 2)
        self.assertEqual(problem.sample_input, 'hello\n')
        self.assertEqual(problem.test_cases, self.PAYLOAD['test_cases'])

    def test_native_superuser_can_create_problem_statement(self):
        superuser = self._make_native_superuser()

        response = self._post_json(
            '/api/supervisor/problem-statements',
            self.PAYLOAD,
            superuser,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['title'], 'Reverse a String')

    def test_week_number_and_sample_input_are_optional(self):
        supervisor = self._make_supervisor()

        response = self._post_json(
            '/api/supervisor/problem-statements',
            {
                'title': 'Hello World',
                'description': 'Print hello.',
                'test_cases': [{'input': '', 'expected_output': 'Hello\n'}],
            },
            supervisor,
        )

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.json()['week_number'])

    def test_create_requires_title_and_description(self):
        supervisor = self._make_supervisor()

        response = self._post_json(
            '/api/supervisor/problem-statements', {'title': 'No description'}, supervisor,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ProblemStatement.objects.count(), 0)

    def test_problem_creation_requires_grading_test_cases(self):
        supervisor = self._make_supervisor()
        payload = {
            'title': 'No tests',
            'description': 'A problem without expected results.',
        }

        response = self._post_json('/api/supervisor/problem-statements', payload, supervisor)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ProblemStatement.objects.count(), 0)

    def test_faculty_cannot_create_problem_statement(self):
        faculty = self._make_faculty()

        response = self._post_json('/api/supervisor/problem-statements', self.PAYLOAD, faculty)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ProblemStatement.objects.count(), 0)

    def test_student_cannot_create_problem_statement(self):
        student = self._make_student()

        response = self._post_json('/api/supervisor/problem-statements', self.PAYLOAD, student)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ProblemStatement.objects.count(), 0)

    def test_unauthenticated_cannot_create_problem_statement(self):
        response = self._post_json('/api/supervisor/problem-statements', self.PAYLOAD)

        self.assertEqual(response.status_code, 401)

    def test_supervisor_can_list_problem_statements(self):
        supervisor = self._make_supervisor()
        self._make_problem(supervisor, title='First')
        self._make_problem(supervisor, title='Second')

        response = self._get('/api/supervisor/problem-statements', supervisor)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertIn('sample_input', response.json()[0])
        self.assertIn('test_cases', response.json()[0])

    def test_student_cannot_use_supervisor_list(self):
        student = self._make_student()

        response = self._get('/api/supervisor/problem-statements', student)

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_list_supervisor_problem_statements(self):
        response = self._get('/api/supervisor/problem-statements')

        self.assertEqual(response.status_code, 401)


class StudentProblemStatementTests(AssignmentsTestBase):
    def test_student_can_list_problem_statements(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        self._make_problem(supervisor, title='First')
        self._make_problem(supervisor, title='Second', week_number=3)

        response = self._get('/api/student/problem-statements', student)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 2)
        # The list stays light: full text is only on the detail view.
        self.assertNotIn('description', body[0])

    def test_student_can_view_problem_statement_detail(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)

        response = self._get(f'/api/student/problem-statements/{problem.pk}', student)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['title'], 'Two Sum')
        self.assertEqual(body['description'], 'Add two numbers.')
        self.assertEqual(body['sample_input'], '1 2\n')
        self.assertNotIn('test_cases', body)

    def test_detail_for_missing_problem_is_404(self):
        student = self._make_student()

        response = self._get('/api/student/problem-statements/9999', student)

        self.assertEqual(response.status_code, 404)

    def test_unapproved_student_cannot_list(self):
        student = self._make_student(approved=False)

        response = self._get('/api/student/problem-statements', student)

        self.assertEqual(response.status_code, 403)

    def test_supervisor_cannot_use_student_endpoints(self):
        supervisor = self._make_supervisor()

        response = self._get('/api/student/problem-statements', supervisor)

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_list_or_view(self):
        supervisor = self._make_supervisor()
        problem = self._make_problem(supervisor)

        self.assertEqual(self._get('/api/student/problem-statements').status_code, 401)
        self.assertEqual(
            self._get(f'/api/student/problem-statements/{problem.pk}').status_code, 401,
        )


class MeetingTests(AssignmentsTestBase):
    def _payload(self, **overrides):
        payload = {
            'title': 'Weekly meetup',
            'notes': 'Bring your laptop.',
            'scheduled_for': (timezone.now() + timedelta(days=3)).isoformat(),
        }
        payload.update(overrides)
        return payload

    def test_supervisor_can_create_meeting(self):
        supervisor = self._make_supervisor()

        response = self._post_json('/api/supervisor/meeting', self._payload(), supervisor)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Meeting.objects.count(), 1)
        self.assertEqual(response.json()['updated_by_name'], 'Sam Supervisor')

    def test_native_superuser_can_create_meeting(self):
        superuser = self._make_native_superuser()

        response = self._post_json(
            '/api/supervisor/meeting',
            self._payload(),
            superuser,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['title'], 'Weekly meetup')

    def test_second_post_updates_the_same_meeting(self):
        supervisor = self._make_supervisor()
        self._post_json('/api/supervisor/meeting', self._payload(), supervisor)

        response = self._post_json(
            '/api/supervisor/meeting', self._payload(title='Rescheduled meetup'), supervisor,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Meeting.objects.count(), 1)
        self.assertEqual(Meeting.objects.get().title, 'Rescheduled meetup')

    def test_supervisor_can_view_current_meeting(self):
        supervisor = self._make_supervisor()
        self._post_json('/api/supervisor/meeting', self._payload(), supervisor)

        response = self._get('/api/supervisor/meeting', supervisor)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Weekly meetup')

    def test_supervisor_gets_404_when_no_meeting_is_scheduled(self):
        supervisor = self._make_supervisor()

        response = self._get('/api/supervisor/meeting', supervisor)

        self.assertEqual(response.status_code, 404)

    def test_meeting_requires_title_and_time(self):
        supervisor = self._make_supervisor()

        response = self._post_json('/api/supervisor/meeting', {'notes': 'x'}, supervisor)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Meeting.objects.count(), 0)

    def test_faculty_cannot_set_meeting(self):
        faculty = self._make_faculty()

        response = self._post_json('/api/supervisor/meeting', self._payload(), faculty)

        self.assertEqual(response.status_code, 403)

    def test_student_cannot_set_meeting(self):
        student = self._make_student()

        response = self._post_json('/api/supervisor/meeting', self._payload(), student)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Meeting.objects.count(), 0)

    def test_unauthenticated_cannot_set_meeting(self):
        response = self._post_json('/api/supervisor/meeting', self._payload())

        self.assertEqual(response.status_code, 401)

    def test_student_can_view_current_meeting(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        self._post_json('/api/supervisor/meeting', self._payload(), supervisor)

        response = self._get('/api/student/meeting', student)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['title'], 'Weekly meetup')
        self.assertEqual(body['notes'], 'Bring your laptop.')

    def test_student_gets_404_when_no_meeting_scheduled(self):
        student = self._make_student()

        response = self._get('/api/student/meeting', student)

        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_cannot_view_meeting(self):
        response = self._get('/api/student/meeting')

        self.assertEqual(response.status_code, 401)
