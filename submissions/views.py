from concurrent.futures import ThreadPoolExecutor

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import close_old_connections
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import StudentProfile
from accounts.permissions import CanViewStudentProgress, IsApprovedStudent
from assignments.models import ProblemStatement

from .models import Submission
from accounts.models import ActivityLog, record_activity
from .serializers import SubmissionCreateSerializer, SubmissionDetailSerializer, SubmissionListSerializer

_grading_executor = ThreadPoolExecutor(max_workers=4)


def _broadcast_submission_status(submission):
    async_to_sync(get_channel_layer().group_send)(
        f'submission_{submission.pk}',
        {
            'type': 'submission.status',
            'status': submission.status,
            'judge0_output': submission.judge0_output,
        },
    )


def _grade_submission(submission_id):
    close_old_connections()
    try:
        submission = Submission.objects.get(pk=submission_id)
        try:
            passed, judge0_output = run_judge0_check(submission)
        except Exception as exc:
            submission.status = Submission.STATUS_PENDING
            submission.judge0_output = str(exc)
            submission.save(update_fields=['status', 'judge0_output'])
            _broadcast_submission_status(submission)
            return

        submission.status = Submission.STATUS_PASSED if passed else Submission.STATUS_FAILED
        submission.judge0_output = judge0_output
        submission.checked_at = timezone.now()
        submission.save(update_fields=['status', 'judge0_output', 'checked_at'])
        _broadcast_submission_status(submission)
    finally:
        close_old_connections()


@api_view(['GET'])
@permission_classes([CanViewStudentProgress])
def supervisor_student_progress(request):
    total_problems = ProblemStatement.objects.count()
    students = StudentProfile.objects.filter(is_approved=True).select_related(
        'user',
    ).prefetch_related(
        Prefetch(
            'submissions',
            queryset=Submission.objects.select_related('problem_statement').order_by(
                '-submitted_at', '-id',
            ),
        ),
    ).order_by('division', 'division_roll_number', 'name', 'id')

    progress = []
    passed_attempts = 0
    failed_attempts = 0
    for student in students:
        submissions = list(student.submissions.all())
        passed_attempts += sum(
            submission.status == Submission.STATUS_PASSED
            for submission in submissions
        )
        failed_attempts += sum(
            submission.status == Submission.STATUS_FAILED
            for submission in submissions
        )
        solved_problem_ids = {
            submission.problem_statement_id
            for submission in submissions
            if submission.status == Submission.STATUS_PASSED
        }
        latest_submission = submissions[0] if submissions else None
        if latest_submission is None:
            progress_status = 'inactive'
        elif latest_submission.status == Submission.STATUS_PASSED:
            progress_status = 'on-track'
        else:
            progress_status = 'needs-review'

        progress.append({
            'id': student.id,
            'name': student.name,
            'enrollment_number': student.enrollment_number,
            'division': student.division,
            'solved_count': len(solved_problem_ids),
            'total_count': total_problems,
            'latest_problem_id': latest_submission.problem_statement_id if latest_submission else None,
            'latest_problem_title': latest_submission.problem_statement.title if latest_submission else None,
            'latest_status': latest_submission.status if latest_submission else None,
            'latest_submitted_at': latest_submission.submitted_at if latest_submission else None,
            'progress_status': progress_status,
        })

    graded_attempts = passed_attempts + failed_attempts
    summary = {
        'active_student_count': len(progress),
        'average_solved': round(
            sum(student['solved_count'] for student in progress) / len(progress), 1,
        ) if progress else 0,
        'pending_review_count': sum(
            student['progress_status'] == 'needs-review' for student in progress
        ),
        'pass_rate': round(passed_attempts / graded_attempts * 100, 1) if graded_attempts else 0,
    }
    return Response({'students': progress, 'summary': summary})


@api_view(['GET'])
@permission_classes([CanViewStudentProgress])
def supervisor_student_submissions(request, student_id):
    student = get_object_or_404(StudentProfile, pk=student_id, is_approved=True)
    submissions = Submission.objects.filter(student=student).select_related(
        'problem_statement',
    )
    return Response(SubmissionListSerializer(submissions, many=True).data)


@api_view(['GET'])
@permission_classes([CanViewStudentProgress])
def supervisor_student_submission_detail(request, student_id, pk):
    submission = get_object_or_404(
        Submission.objects.select_related('problem_statement'),
        pk=pk,
        student_id=student_id,
        student__is_approved=True,
    )
    return Response(SubmissionDetailSerializer(submission).data)


@api_view(['POST'])
@permission_classes([IsApprovedStudent])
def student_submit_problem(request, pk):
    problem = get_object_or_404(ProblemStatement, pk=pk)
    student = request.user.student_profile
    if Submission.objects.filter(
        student=student,
        problem_statement=problem,
        status=Submission.STATUS_PASSED,
    ).exists():
        return Response(
            {'detail': 'This problem has already been completed.'},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = SubmissionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if not problem.test_cases:
        return Response(
            {'detail': 'This problem has no grading test cases configured yet.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if serializer.validated_data['language'] == Submission.LANGUAGE_HTML:
        return Response(
            {'detail': 'HTML cannot be automatically graded. Choose an executable language.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    submission = Submission.objects.create(
        student=student,
        problem_statement=problem,
        language=serializer.validated_data['language'],
        code=serializer.validated_data['code'],
        status=Submission.STATUS_PENDING,
    )
    record_activity(
        request.user,
        ActivityLog.CATEGORY_REVIEW,
        'submission_created',
        f'{student.name} submitted code for {problem.title}.',
        target=submission,
    )
<<<<<<< HEAD
    try:
        passed, judge0_output = run_judge0_check(submission)
    except Exception as exc:
        submission.status = Submission.STATUS_PENDING
        submission.judge0_output = str(exc)
        submission.save(update_fields=['status', 'judge0_output'])
        _broadcast_submission_status(submission)
        return Response(
            {'detail': 'Your code was saved, but automatic grading is unavailable. Try again later.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    submission.status = Submission.STATUS_PASSED if passed else Submission.STATUS_FAILED
    submission.judge0_output = judge0_output
    submission.checked_at = timezone.now()
    submission.save(update_fields=['status', 'judge0_output', 'checked_at'])
    _broadcast_submission_status(submission)
=======
>>>>>>> 1c30e87 (..)

    return Response(
        SubmissionDetailSerializer(submission).data,
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['POST'])
@permission_classes([IsApprovedStudent])
def student_submit_problem_live(request, pk):
    problem = get_object_or_404(ProblemStatement, pk=pk)
    student = request.user.student_profile
    if Submission.objects.filter(
        student=student,
        problem_statement=problem,
        status=Submission.STATUS_PASSED,
    ).exists():
        return Response(
            {'detail': 'This problem has already been completed.'},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = SubmissionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if not problem.test_cases:
        return Response(
            {'detail': 'This problem has no grading test cases configured yet.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if serializer.validated_data['language'] == Submission.LANGUAGE_HTML:
        return Response(
            {'detail': 'HTML cannot be automatically graded. Choose an executable language.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    submission = Submission.objects.create(
        student=student,
        problem_statement=problem,
        language=serializer.validated_data['language'],
        code=serializer.validated_data['code'],
        status=Submission.STATUS_CHECKING,
    )
    _grading_executor.submit(_grade_submission, submission.pk)
    return Response(
        SubmissionDetailSerializer(submission).data,
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def student_submissions(request):
    submissions = Submission.objects.filter(student=request.user.student_profile).select_related(
        'problem_statement',
    )
    return Response(SubmissionListSerializer(submissions, many=True).data)


@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def student_submission_detail(request, pk):
    submission = get_object_or_404(
        Submission,
        pk=pk,
        student=request.user.student_profile,
    )
    return Response(SubmissionDetailSerializer(submission).data)
