from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsApprovedStudent, IsSupervisor
from accounts.models import ActivityLog, record_activity

from .models import Announcement, Meeting, ProblemStatement
from .serializers import (
    AnnouncementCreateSerializer,
    AnnouncementSerializer,
    MeetingUpdateSerializer,
    ProblemStatementCreateSerializer,
    ProblemStatementUpdateSerializer,
    StudentMeetingSerializer,
    StudentProblemStatementDetailSerializer,
    StudentProblemStatementListSerializer,
    SupervisorMeetingSerializer,
    SupervisorProblemStatementSerializer,
)


def _current_meeting():
    return Meeting.objects.filter(slot=1).first() or Meeting.objects.order_by('slot', 'id').first()


# --- Supervisor endpoints ---

@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
@permission_classes([IsSupervisor])
def supervisor_problem_statements(request, pk=None):
    if request.method in ('PATCH', 'DELETE'):
        if pk is None:
            return Response(
                {'detail': 'A problem statement id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        problem = get_object_or_404(ProblemStatement, pk=pk)
        if request.method == 'DELETE':
            title = problem.title
            problem.delete()
            record_activity(
                request.user,
                ActivityLog.CATEGORY_ASSIGNMENT,
                'problem_deleted',
                f'{title} was deleted from the problem statements.',
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = ProblemStatementUpdateSerializer(
            problem,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_activity(
            request.user,
            ActivityLog.CATEGORY_ASSIGNMENT,
            'problem_updated',
            f'{problem.title} was updated.',
            target=problem,
        )
        return Response(SupervisorProblemStatementSerializer(problem).data)

    if request.method == 'POST':
        serializer = ProblemStatementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        problem = ProblemStatement.objects.create(
            created_by=getattr(request.user, 'admin_profile', None),
            **serializer.validated_data,
        )
        record_activity(
            request.user,
            ActivityLog.CATEGORY_ASSIGNMENT,
            'problem_created',
            f'{problem.title} was uploaded as a problem statement.',
            target=problem,
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

    meeting = Meeting.objects.filter(slot=data.get('slot', 1)).first()
    created = meeting is None
    if created:
        meeting = Meeting()

    meeting.title = data['title']
    meeting.notes = data.get('notes', '')
    meeting.scheduled_for = data['scheduled_for']
    meeting.slot = data.get('slot', 1)
    meeting.updated_by = getattr(request.user, 'admin_profile', None)
    meeting.save()
    record_activity(
        request.user,
        ActivityLog.CATEGORY_MEETING,
        'meeting_updated',
        f'Meeting "{meeting.title}" was scheduled or updated.',
        target=meeting,
    )

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


@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def student_updates(request):
    meetings = Meeting.objects.order_by('slot', 'scheduled_for')[:2]
    announcements = Announcement.objects.filter(is_published=True)[:20]
    return Response({
        'meetings': StudentMeetingSerializer(meetings, many=True).data,
        'announcements': AnnouncementSerializer(announcements, many=True).data,
    })


@api_view(['GET', 'POST'])
@permission_classes([IsSupervisor])
def supervisor_announcements(request):
    if request.method == 'GET':
        return Response(AnnouncementSerializer(Announcement.objects.all()[:100], many=True).data)
    serializer = AnnouncementCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    announcement = Announcement.objects.create(
        created_by=getattr(request.user, 'admin_profile', None),
        **serializer.validated_data,
    )
    return Response(AnnouncementSerializer(announcement).data, status=status.HTTP_201_CREATED)
