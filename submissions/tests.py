import json
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from accounts.models import AdminProfile, StudentProfile
from assignments.models import Meeting, ProblemStatement
from submissions.models import Submission


class SubmissionsTestBase(TestCase):
    def _make_admin(self, email, staff_type, name='Staff Member'):
        user = self._make_user(email)
        AdminProfile.objects.create(
            user=user,
            name=name,
            phone='1',
            is_approved=True,
            staff_type=staff_type,
        )
        return user

    def _make_supervisor(self):
        return self._make_admin(
            'supervisor@example.com',
            AdminProfile.STAFF_SUPERVISOR,
            name='Sam Supervisor',
        )

    def _make_faculty(self):
        return self._make_admin('faculty@example.com', AdminProfile.STAFF_FACULTY)

    def _make_user(self, email):
        from django.contrib.auth import get_user_model

        return get_user_model().objects.create_user(
            username=email,
            email=email,
            password='A-secure-password-123',
        )

    def _make_student(self, email='student@example.com', enrollment='ENR001', approved=True):
        user = self._make_user(email)
        StudentProfile.objects.create(
            user=user,
            name='Test Student',
            division='A',
            division_roll_number='1',
            branch='CS',
            phone='1',
            enrollment_number=enrollment,
            is_approved=approved,
        )
        return user

    def _make_problem(self, supervisor_user, title='Two Sum', **extra):
        return ProblemStatement.objects.create(
            title=title,
            description='Add two numbers.',
            sample_input='1 2\n',
            created_by=supervisor_user.admin_profile,
            **extra,
        )

    def _token_header(self, user):
        from rest_framework.authtoken.models import Token

        token, _ = Token.objects.get_or_create(user=user)
        return {'HTTP_AUTHORIZATION': f'Bearer {token.key}'}

    def _post_json(self, path, payload, user=None):
        extra = self._token_header(user) if user else {}
        return self.client.post(
            path,
            data=json.dumps(payload),
            content_type='application/json',
            **extra,
        )

    def _get(self, path, user=None):
        extra = self._token_header(user) if user else {}
        return self.client.get(path, **extra)


class StudentSubmissionEndpointTests(SubmissionsTestBase):
    def test_student_can_submit_problem_code(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)

        with patch('submissions.views.Submission.objects.create') as fake_create:
            fake_create.return_value = Submission.objects.create(
                student=student.student_profile,
                problem_statement=problem,
                language='c',
                code='int main(){return 0;}',
                status=Submission.STATUS_PENDING,
            )

            response = self._post_json(
                f'/api/student/problem-statements/{problem.pk}/submit',
                {'language': 'c', 'code': 'int main(){return 0;}'},
                student,
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.filter(student=student.student_profile).count(), 1)

    def test_submission_does_not_trigger_judge0_synchronously(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)

        with patch('submissions.judge0.run_judge0_check') as fake_check:
            response = self._post_json(
                f'/api/student/problem-statements/{problem.pk}/submit',
                {'language': 'c', 'code': 'int main(){return 0;}'},
                student,
            )

        self.assertEqual(response.status_code, 201)
        fake_check.assert_not_called()

    def test_student_can_list_their_own_submissions(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        other_student = self._make_student(email='other@example.com', enrollment='ENR002')
        problem = self._make_problem(supervisor)

        Submission.objects.create(
            student=student.student_profile,
            problem_statement=problem,
            language='c',
            code='int main(){return 0;}',
            status=Submission.STATUS_PENDING,
        )
        Submission.objects.create(
            student=other_student.student_profile,
            problem_statement=problem,
            language='html',
            code='<h1>Hello</h1>',
            status=Submission.STATUS_SUBMITTED,
        )

        response = self._get('/api/student/submissions', student)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]['language'], 'c')

    def test_student_cannot_view_another_students_submission(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        other_student = self._make_student(email='other@example.com', enrollment='ENR002')
        problem = self._make_problem(supervisor)
        submission = Submission.objects.create(
            student=other_student.student_profile,
            problem_statement=problem,
            language='c',
            code='int main(){return 0;}',
            status=Submission.STATUS_PENDING,
        )

        response = self._get(f'/api/student/submissions/{submission.pk}', student)

        self.assertEqual(response.status_code, 404)

    def test_unapproved_student_cannot_submit(self):
        supervisor = self._make_supervisor()
        student = self._make_student(approved=False)
        problem = self._make_problem(supervisor)

        response = self._post_json(
            f'/api/student/problem-statements/{problem.pk}/submit',
            {'language': 'c', 'code': 'int main(){return 0;}'},
            student,
        )

        self.assertEqual(response.status_code, 403)


class SubmissionCheckCommandTests(SubmissionsTestBase):
    def test_check_submissions_marks_c_code_as_passed(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)
        submission = Submission.objects.create(
            student=student.student_profile,
            problem_statement=problem,
            language='c',
            code='int main(){return 0;}',
            status=Submission.STATUS_PENDING,
        )

        with patch('submissions.management.commands.check_submissions.run_judge0_check', return_value=(True, 'hello')):
            call_command('check_submissions')

        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.STATUS_PASSED)
        self.assertEqual(submission.judge0_output, 'hello')
        self.assertIsNotNone(submission.checked_at)

    def test_check_submissions_marks_c_code_as_failed(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)
        submission = Submission.objects.create(
            student=student.student_profile,
            problem_statement=problem,
            language='c',
            code='int main(){return 0;}',
            status=Submission.STATUS_PENDING,
        )

        with patch('submissions.management.commands.check_submissions.run_judge0_check', return_value=(False, 'wrong output')):
            call_command('check_submissions')

        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.STATUS_FAILED)
        self.assertEqual(submission.judge0_output, 'wrong output')

    def test_check_submissions_marks_html_as_submitted(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)
        submission = Submission.objects.create(
            student=student.student_profile,
            problem_statement=problem,
            language='html',
            code='<h1>Hello</h1>',
            status=Submission.STATUS_PENDING,
        )

        with patch('submissions.management.commands.check_submissions.run_judge0_check') as fake_check:
            call_command('check_submissions')

        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.STATUS_SUBMITTED)
        fake_check.assert_not_called()
