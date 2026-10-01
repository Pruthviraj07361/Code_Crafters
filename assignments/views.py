from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsApprovedStudent, IsSupervisor

from .models import Meeting, ProblemStatement
from .serializers import (
    MeetingUpdateSerializer,
    ProblemStatementCreateSerializer,
    StudentMeetingSerializer,
    StudentProblemStatementDetailSerializer,
    StudentProblemStatementListSerializer,
    SupervisorMeetingSerializer,
    SupervisorProblemStatementSerializer,
)


def _current_meeting():
    return Meeting.objects.order_by('-id').first()


# --- Supervisor endpoints ---

@api_view(['GET', 'POST'])
@permission_classes([IsSupervisor])
def supervisor_problem_statements(request):
    if request.method == 'POST':
        serializer = ProblemStatementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        problem = ProblemStatement.objects.create(
            created_by=request.user.admin_profile,
            **serializer.validated_data,
        )
        return Response(
            SupervisorProblemStatementSerializer(problem).data,
            status=status.HTTP_201_CREATED,
        )

    queryset = ProblemStatement.objects.select_related('created_by')
    return Response(SupervisorProblemStatementSerializer(queryset, many=True).data)


@api_view(['GET', 'POST'])
@permission_classes([IsSupervisor])
def supervisor_meeting(request):
    if request.method == 'GET':
        meeting = _current_meeting()
        if meeting is None:
            return Response(
                {'detail': 'No meeting has been scheduled yet.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(SupervisorMeetingSerializer(meeting).data)

    serializer = MeetingUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    meeting = _current_meeting()
    created = meeting is None
    if created:
        meeting = Meeting()

    meeting.title = data['title']
    meeting.notes = data.get('notes', '')
    meeting.scheduled_for = data['scheduled_for']
    meeting.updated_by = request.user.admin_profile
    meeting.save()

    return Response(
        SupervisorMeetingSerializer(meeting).data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


# --- Student endpoints ---

@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def student_problem_statements(request):
    queryset = ProblemStatement.objects.all()
    return Response(StudentProblemStatementListSerializer(queryset, many=True).data)


@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def student_problem_statement_detail(request, pk):
    problem = get_object_or_404(ProblemStatement, pk=pk)
    return Response(StudentProblemStatementDetailSerializer(problem).data)


@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def student_meeting(request):
    meeting = _current_meeting()
    if meeting is None:
        return Response(
            {'detail': 'No meeting has been scheduled yet.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(StudentMeetingSerializer(meeting).data)
