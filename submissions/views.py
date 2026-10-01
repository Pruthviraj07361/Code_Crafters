from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsApprovedStudent
from assignments.models import ProblemStatement

from .models import Submission
from .serializers import SubmissionCreateSerializer, SubmissionDetailSerializer, SubmissionListSerializer


@api_view(['POST'])
@permission_classes([IsApprovedStudent])
def student_submit_problem(request, pk):
    problem = get_object_or_404(ProblemStatement, pk=pk)
    serializer = SubmissionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    submission = Submission.objects.create(
        student=request.user.student_profile,
        problem_statement=problem,
        language=serializer.validated_data['language'],
        code=serializer.validated_data['code'],
        status=Submission.STATUS_PENDING,
    )

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
