from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsApprovedStudent
from assignments.models import ProblemStatement

from .judge0 import run_judge0_check
from .models import Submission
from .serializers import SubmissionCreateSerializer, SubmissionDetailSerializer, SubmissionListSerializer


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
        status=Submission.STATUS_CHECKING,
    )
    try:
        passed, judge0_output = run_judge0_check(submission)
    except Exception as exc:
        submission.status = Submission.STATUS_PENDING
        submission.judge0_output = str(exc)
        submission.save(update_fields=['status', 'judge0_output'])
        return Response(
            {'detail': 'Your code was saved, but automatic grading is unavailable. Try again later.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    submission.status = Submission.STATUS_PASSED if passed else Submission.STATUS_FAILED
    submission.judge0_output = judge0_output
    submission.checked_at = timezone.now()
    submission.save(update_fields=['status', 'judge0_output', 'checked_at'])

    return Response(
        SubmissionDetailSerializer(submission).data,
        status=status.HTTP_201_CREATED,
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
