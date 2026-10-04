import json
from unittest.mock import Mock, patch

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from requests import Timeout

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
            test_cases=extra.pop(
                'test_cases', [{'input': '1 2\n', 'expected_output': '3\n'}]
            ),
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

        with patch(
            'submissions.views.run_judge0_check',
            return_value=(True, 'All 1 test cases passed.'),
        ) as fake_check:
            response = self._post_json(
                f'/api/student/problem-statements/{problem.pk}/submit',
                {'language': 'c', 'code': 'int main(){return 0;}'},
                student,
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.filter(student=student.student_profile).count(), 1)
        self.assertEqual(response.json()['status'], Submission.STATUS_PASSED)
        fake_check.assert_called_once()

    def test_incorrect_code_is_saved_as_failed(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)

        with patch(
            'submissions.views.run_judge0_check',
            return_value=(False, 'Test case 1 failed: Wrong Answer'),
        ):
            response = self._post_json(
                f'/api/student/problem-statements/{problem.pk}/submit',
                {'language': 'c', 'code': 'int main(){return 0;}'},
                student,
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], Submission.STATUS_FAILED)
        self.assertEqual(Submission.objects.get().status, Submission.STATUS_FAILED)

    def test_problem_without_test_cases_cannot_be_submitted(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor, test_cases=[])

        with patch('submissions.views.run_judge0_check') as fake_check:
            response = self._post_json(
                f'/api/student/problem-statements/{problem.pk}/submit',
                {'language': 'c', 'code': 'int main(){return 0;}'},
                student,
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)
        fake_check.assert_not_called()

    def test_grader_outage_keeps_submission_pending(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)

        with patch(
            'submissions.views.run_judge0_check',
            side_effect=RuntimeError('Judge0 is unavailable.'),
        ):
            response = self._post_json(
                f'/api/student/problem-statements/{problem.pk}/submit',
                {'language': 'c', 'code': 'int main(){return 0;}'},
                student,
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(Submission.objects.get().status, Submission.STATUS_PENDING)

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


class LiveSubmissionEndpointTests(SubmissionsTestBase):
    def test_live_submit_returns_submission_before_grading_finishes(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)

        with patch('submissions.views._grading_executor.submit') as submit_job:
            response = self._post_json(
                f'/api/student/problem-statements/{problem.pk}/submit-live',
                {'language': 'c', 'code': 'int main(void) { return 0; }'},
                student,
            )

        submission = Submission.objects.get()
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()['id'], submission.pk)
        self.assertEqual(response.json()['status'], Submission.STATUS_CHECKING)
        submit_job.assert_called_once()
        grader, submission_id = submit_job.call_args.args
        self.assertEqual(grader.__name__, '_grade_submission')
        self.assertEqual(submission_id, submission.pk)

    def test_synchronous_submit_broadcasts_the_checked_result(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)

        with (
            patch(
                'submissions.views.run_judge0_check',
                return_value=(False, 'Test case 1 failed: Wrong Answer'),
            ),
            patch('submissions.views._broadcast_submission_status') as broadcast,
        ):
            response = self._post_json(
                f'/api/student/problem-statements/{problem.pk}/submit',
                {'language': 'c', 'code': 'int main(void) { return 0; }'},
                student,
            )

        self.assertEqual(response.status_code, 201)
        broadcast.assert_called_once()
        broadcast_submission = broadcast.call_args.args[0]
        self.assertEqual(broadcast_submission.status, Submission.STATUS_FAILED)
        self.assertEqual(
            broadcast_submission.judge0_output,
            'Test case 1 failed: Wrong Answer',
        )


class SubmissionWebSocketTests(SubmissionsTestBase, TransactionTestCase):
    def _communicator(self, submission, user):
        from rest_framework.authtoken.models import Token

        token, _ = Token.objects.get_or_create(user=user)
        from config.asgi import application

        return WebsocketCommunicator(
            application,
            f'/ws/submissions/{submission.pk}/?token={token.key}',
        )

    def test_owner_receives_initial_status_and_later_result(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        problem = self._make_problem(supervisor)
        submission = Submission.objects.create(
            student=student.student_profile,
            problem_statement=problem,
            language='c',
            code='int main(void) { return 0; }',
            status=Submission.STATUS_CHECKING,
        )
        communicator = self._communicator(submission, student)

        async def connect_and_receive():
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            initial = await communicator.receive_json_from()
            await get_channel_layer().group_send(
                f'submission_{submission.pk}',
                {
                    'type': 'submission.status',
                    'status': Submission.STATUS_PASSED,
                    'judge0_output': 'All test cases passed.',
                },
            )
            result = await communicator.receive_json_from()
            await communicator.disconnect()
            return initial, result

        initial, result = async_to_sync(connect_and_receive)()

        self.assertEqual(initial['status'], Submission.STATUS_CHECKING)
        self.assertEqual(result, {
            'status': Submission.STATUS_PASSED,
            'judge0_output': 'All test cases passed.',
        })

    def test_other_student_is_rejected_but_supervisor_is_allowed(self):
        supervisor = self._make_supervisor()
        owner = self._make_student()
        other_student = self._make_student('other@example.com', 'ENR002')
        problem = self._make_problem(supervisor)
        submission = Submission.objects.create(
            student=owner.student_profile,
            problem_statement=problem,
            language='c',
            code='int main(void) { return 0; }',
            status=Submission.STATUS_PENDING,
        )
        unauthorized = self._communicator(submission, other_student)
        authorized_staff = self._communicator(submission, supervisor)

        async def check_access():
            denied, close_code = await unauthorized.connect()
            allowed, _ = await authorized_staff.connect()
            if allowed:
                await authorized_staff.receive_json_from()
                await authorized_staff.disconnect()
            return denied, close_code, allowed

        denied, close_code, allowed = async_to_sync(check_access)()

        self.assertFalse(denied)
        self.assertEqual(close_code, 4403)
        self.assertTrue(allowed)


class SupervisorStudentProgressEndpointTests(SubmissionsTestBase):
    def test_supervisor_receives_approved_students_and_real_submission_progress(self):
        supervisor = self._make_supervisor()
        student = self._make_student(
            email='alex@example.com',
            enrollment='ALEX001',
        )
        self._make_student(
            email='pending@example.com',
            enrollment='PENDING001',
            approved=False,
        )
        problem = self._make_problem(supervisor, title='Reverse a String')
        Submission.objects.create(
            student=student.student_profile,
            problem_statement=problem,
            language='c',
            code='int main(void) { return 0; }',
            status=Submission.STATUS_PASSED,
        )

        response = self._get('/api/supervisor/student-progress', supervisor)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body['students']), 1)
        progress = body['students'][0]
        self.assertEqual(progress['name'], 'Test Student')
        self.assertEqual(progress['enrollment_number'], 'ALEX001')
        self.assertEqual(progress['solved_count'], 1)
        self.assertEqual(progress['total_count'], 1)
        self.assertEqual(progress['latest_problem_title'], 'Reverse a String')
        self.assertEqual(progress['progress_status'], 'on-track')
        self.assertEqual(body['summary'], {
            'active_student_count': 1,
            'average_solved': 1.0,
            'pending_review_count': 0,
            'pass_rate': 100.0,
        })

    def test_progress_lists_each_student_once_and_orders_by_division(self):
        supervisor = self._make_supervisor()
        first_student = self._make_student('first@example.com', 'FIRST001')
        second_student = self._make_student('second@example.com', 'SECOND001')
        third_student = self._make_student('third@example.com', 'THIRD001')
        first_student.student_profile.division = 'D2'
        first_student.student_profile.division_roll_number = '1'
        first_student.student_profile.save()
        second_student.student_profile.division = 'D1'
        second_student.student_profile.division_roll_number = '2'
        second_student.student_profile.save()
        third_student.student_profile.division = 'D1'
        third_student.student_profile.division_roll_number = '1'
        third_student.student_profile.save()
        first_problem = self._make_problem(supervisor, title='Problem One')
        second_problem = self._make_problem(supervisor, title='Problem Two')
        for problem in (first_problem, second_problem):
            Submission.objects.create(
                student=first_student.student_profile,
                problem_statement=problem,
                language='c',
                code='int main(void) { return 0; }',
                status=Submission.STATUS_PASSED,
            )

        response = self._get('/api/supervisor/student-progress', supervisor)

        self.assertEqual(response.status_code, 200)
        students = response.json()['students']
        self.assertEqual(
            [student['enrollment_number'] for student in students],
            ['THIRD001', 'SECOND001', 'FIRST001'],
        )
        first_student_progress = students[-1]
        self.assertEqual(first_student_progress['solved_count'], 2)

    def test_superuser_can_view_student_progress(self):
        superuser = self._make_admin(
            'admin@example.com', AdminProfile.STAFF_SUPERUSER,
        )

        response = self._get('/api/supervisor/student-progress', superuser)

        self.assertEqual(response.status_code, 200)

    def test_faculty_can_view_student_progress(self):
        faculty = self._make_faculty()

        response = self._get('/api/supervisor/student-progress', faculty)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['students'], [])

    def test_student_cannot_access_supervisor_progress(self):
        student = self._make_student()

        response = self._get('/api/supervisor/student-progress', student)

        self.assertEqual(response.status_code, 403)


class SupervisorSubmissionReviewEndpointTests(SubmissionsTestBase):
    def test_staff_can_choose_a_submission_and_load_its_code(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        first_problem = self._make_problem(supervisor, title='Reverse a String')
        second_problem = self._make_problem(supervisor, title='Prime Number')
        first_submission = Submission.objects.create(
            student=student.student_profile,
            problem_statement=first_problem,
            language='python',
            code='print("reversed")',
            status=Submission.STATUS_FAILED,
        )
        Submission.objects.create(
            student=student.student_profile,
            problem_statement=second_problem,
            language='c',
            code='int main(void) { return 0; }',
            status=Submission.STATUS_PASSED,
        )

        response = self._get(
            f'/api/supervisor/students/{student.student_profile.pk}/submissions',
            supervisor,
        )

        self.assertEqual(response.status_code, 200)
        choices = response.json()
        self.assertEqual(len(choices), 2)
        self.assertEqual(
            {choice['problem_title'] for choice in choices},
            {'Reverse a String', 'Prime Number'},
        )
        self.assertTrue(all('code' not in choice for choice in choices))

        detail_response = self._get(
            f'/api/supervisor/students/{student.student_profile.pk}/submissions/{first_submission.pk}',
            supervisor,
        )

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()['code'], 'print("reversed")')
        self.assertEqual(detail_response.json()['problem_title'], 'Reverse a String')

    def test_student_cannot_review_submissions_and_submission_is_student_scoped(self):
        supervisor = self._make_supervisor()
        student = self._make_student()
        other_student = self._make_student('other@example.com', 'ENR002')
        problem = self._make_problem(supervisor)
        submission = Submission.objects.create(
            student=student.student_profile,
            problem_statement=problem,
            language='python',
            code='print("hello")',
            status=Submission.STATUS_SUBMITTED,
        )

        list_response = self._get(
            f'/api/supervisor/students/{student.student_profile.pk}/submissions',
            student,
        )
        wrong_student_response = self._get(
            f'/api/supervisor/students/{other_student.student_profile.pk}/submissions/{submission.pk}',
            supervisor,
        )

        self.assertEqual(list_response.status_code, 403)
        self.assertEqual(wrong_student_response.status_code, 404)


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


class Judge0CheckTests(TestCase):
    def setUp(self):
        self.submission = Mock()
        self.submission.language = 'c'
        self.submission.code = 'int main(void) { return 0; }'
        self.submission.problem_statement.test_cases = [
            {'input': '1 2\n', 'expected_output': '3\n'},
            {'input': '3 4\n', 'expected_output': '7\n'},
        ]

    @patch(
        'submissions.judge0.get_judge0_config',
        return_value={'api_key': 'test-key', 'base_url': 'https://judge.example/api'},
    )
    @patch('submissions.judge0.requests.post')
    def test_all_test_cases_must_be_accepted(self, mock_post, mock_config):
        response = Mock(ok=True, status_code=201)
        response.json.return_value = {'status': {'id': 3, 'description': 'Accepted'}}
        mock_post.return_value = response

        from submissions.judge0 import run_judge0_check

        passed, output = run_judge0_check(self.submission)

        self.assertTrue(passed)
        self.assertIn('2 test cases passed', output)
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(
            mock_post.call_args_list[0].kwargs['json']['expected_output'], '3\n'
        )
        self.assertTrue(all(
            call.kwargs['timeout'] == (5, 30)
            for call in mock_post.call_args_list
        ))

    @patch(
        'submissions.judge0.get_judge0_config',
        return_value={'api_key': 'test-key', 'base_url': 'https://judge.example/api'},
    )
    @patch('submissions.judge0.requests.post')
    def test_transient_timeout_is_retried_once(self, mock_post, mock_config):
        from submissions.judge0 import run_judge0_check

        accepted = Mock(ok=True, status_code=201)
        accepted.json.return_value = {'status': {'id': 3, 'description': 'Accepted'}}
        mock_post.side_effect = [Timeout(), accepted, accepted]

        passed, output = run_judge0_check(self.submission)

        self.assertTrue(passed)
        self.assertEqual(mock_post.call_count, 3)
        self.assertTrue(all(
            call.kwargs['timeout'] == (5, 30)
            for call in mock_post.call_args_list
        ))

    @patch(
        'submissions.judge0.get_judge0_config',
        return_value={'api_key': 'test-key', 'base_url': 'https://judge.example/api'},
    )
    @patch('submissions.judge0.requests.post', side_effect=Timeout('private transport details'))
    def test_final_timeout_raises_a_clean_error(self, mock_post, mock_config):
        from submissions.judge0 import run_judge0_check

        with self.assertRaisesRegex(
            RuntimeError,
            '^Judge0 is temporarily unavailable\\. Please retry your submission in a moment\\.$',
        ):
            run_judge0_check(self.submission)

        self.assertEqual(mock_post.call_count, 2)

    @patch(
        'submissions.judge0.get_judge0_config',
        return_value={'api_key': 'test-key', 'base_url': 'https://judge.example/api'},
    )
    @patch('submissions.judge0.requests.post')
    def test_wrong_answer_fails_without_running_later_cases(self, mock_post, mock_config):
        response = Mock(ok=True, status_code=201)
        response.json.return_value = {'status': {'id': 4, 'description': 'Wrong Answer'}}
        mock_post.return_value = response

        from submissions.judge0 import run_judge0_check

        passed, output = run_judge0_check(self.submission)

        self.assertFalse(passed)
        self.assertIn('Test case 1 failed', output)
        self.assertEqual(mock_post.call_count, 1)

    @patch.dict('os.environ', {'JUDGE0_URL': 'http://localhost:2358'}, clear=False)
    def test_get_judge0_config_accepts_self_hosted_url_alias(self):
        from submissions.judge0 import get_judge0_config

        config = get_judge0_config()

        self.assertEqual(config['base_url'], 'http://localhost:2358')
        self.assertEqual(config['api_key'], '')
