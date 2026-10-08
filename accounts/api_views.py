from datetime import date

from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import ActivityLog, AdminProfile, StudentProfile, record_activity
from .permissions import IsFaculty, IsFacultyOrSuperuser, IsSuperuser
from .serializers import (
    AdminRegisterSerializer,
    LoginSerializer,
    PendingStaffSerializer,
    PendingStudentSerializer,
    StaffRoleAssignSerializer,
    StudentApprovalActionSerializer,
    ActivityLogSerializer,
    StudentProfileUpdateSerializer,
    StudentRegisterSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_student(request):
    serializer = StudentRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
        {'detail': 'Registration received, pending approval.'},
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def register_admin(request):
    serializer = AdminRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
        {'detail': 'Registration received, pending admin approval.'},
        status=status.HTTP_201_CREATED,
    )


def _serialize_user(user):
    """Build the {user: {...}} payload the frontend uses to decide which
    role's routes/pages to show. `role` is one of:
    'student', 'faculty', 'supervisor', 'superuser'."""
    if user.is_superuser:
        return {
            'id': user.id,
            'email': user.email,
            'role': 'superuser',
            'name': user.get_full_name() or user.username,
            'phone': '',
        }

    student_profile = getattr(user, 'student_profile', None)
    if student_profile is not None:
        return {
            'id': user.id,
            'email': user.email,
            'role': 'student',
            'name': student_profile.name,
            'division': student_profile.division,
            'division_roll_number': student_profile.division_roll_number,
            'branch': student_profile.branch,
            'phone': student_profile.phone,
            'enrollment_number': student_profile.enrollment_number,
            'semester': student_profile.semester,
        }

    admin_profile = getattr(user, 'admin_profile', None)
    if admin_profile is not None:
        return {
            'id': user.id,
            'email': user.email,
            'role': admin_profile.staff_type,
            'name': admin_profile.name,
            'phone': admin_profile.phone,
        }

    return None


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Both StudentRegisterSerializer and AdminRegisterSerializer create the
    # User with username=email, so email doubles as the login identifier.
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    user = authenticate(
        request,
        username=email,
        password=password,
    )
    if user is None:
        account = get_user_model().objects.filter(email__iexact=email).first()
        if account is not None:
            user = authenticate(
                request,
                username=account.get_username(),
                password=password,
            )
    if user is None:
        return Response(
            {'detail': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {'detail': 'This account has been deactivated.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    student_profile = getattr(user, 'student_profile', None)
    admin_profile = getattr(user, 'admin_profile', None)

    if user.is_superuser:
        pass
    elif student_profile is not None:
        if not student_profile.is_approved:
            return Response(
                {'detail': 'Your registration is pending approval.'},
                status=status.HTTP_403_FORBIDDEN,
            )
    elif admin_profile is not None:
        if not admin_profile.is_approved or not admin_profile.staff_type:
            return Response(
                {'detail': 'Your registration is pending admin approval.'},
                status=status.HTTP_403_FORBIDDEN,
            )
    elif admin_profile is None:
        # Shouldn't happen via the two register endpoints above, but covers
        # e.g. accounts created directly in Django admin without a profile.
        return Response(
            {'detail': 'No student or admin profile is linked to this account.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': _serialize_user(user)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = _serialize_user(request.user)
    if user is None:
        return Response(
            {'detail': 'No student or admin profile is linked to this account.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return Response(user)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_student_profile(request):
    profile = getattr(request.user, 'student_profile', None)
    if profile is None or not profile.is_approved:
        return Response(
            {'detail': 'Only approved students can update this profile.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = StudentProfileUpdateSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    record_activity(
        request.user,
        ActivityLog.CATEGORY_PROFILE,
        'profile_updated',
        f'{profile.name} updated their academic profile.',
        target=profile,
    )
    return Response(_serialize_user(request.user))


@api_view(['GET'])
@permission_classes([IsFacultyOrSuperuser])
def activity_log(request):
    queryset = ActivityLog.objects.select_related('actor', 'actor__admin_profile')
    category = request.query_params.get('category')
    since = request.query_params.get('since')
    until = request.query_params.get('until')
    try:
        since_date = date.fromisoformat(since) if since else None
        until_date = date.fromisoformat(until) if until else None
    except ValueError:
        return Response(
            {'detail': 'Dates must use YYYY-MM-DD format.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if since_date and until_date and since_date > until_date:
        return Response(
            {'detail': 'The start date cannot be after the end date.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if category and category != 'all':
        valid_categories = {choice[0] for choice in ActivityLog.CATEGORY_CHOICES}
        if category not in valid_categories:
            return Response(
                {'detail': 'Unknown activity category.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.filter(category=category)
    if since:
        queryset = queryset.filter(created_at__date__gte=since_date)
    if until:
        queryset = queryset.filter(created_at__date__lte=until_date)
    queryset = queryset[:100]
    return Response(ActivityLogSerializer(queryset, many=True).data)


@api_view(['GET'])
@permission_classes([IsFacultyOrSuperuser])
def pending_students(request):
    queryset = StudentProfile.objects.filter(
        is_approved=False,
        user__is_active=True,
    ).select_related('user')
    serializer = PendingStudentSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsFacultyOrSuperuser])
def approve_student(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    serializer = StudentApprovalActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if serializer.validated_data['approved']:
        profile.is_approved = True
        profile.save(update_fields=['is_approved'])
        record_activity(
            request.user,
            ActivityLog.CATEGORY_DECISION,
            'student_approved',
            f'{profile.name} was approved for portal access.',
            target=profile,
        )
        return Response({'detail': f'{profile.name} has been approved.'})

    # Rejected: deactivate the account rather than deleting it, so the
    # registration data isn't lost and a faculty member can revisit it.
    profile.user.is_active = False
    profile.user.save(update_fields=['is_active'])
    record_activity(
        request.user,
        ActivityLog.CATEGORY_DECISION,
        'student_rejected',
        f'{profile.name} registration was rejected.',
        target=profile,
    )
    return Response({'detail': f'{profile.name}\u2019s registration has been rejected.'})


@api_view(['GET'])
@permission_classes([IsSuperuser])
def pending_staff(request):
    queryset = AdminProfile.objects.filter(
        is_approved=False,
        user__is_active=True,
    ).select_related('user')
    serializer = PendingStaffSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsSuperuser])
def assign_staff_role(request, pk):
    profile = get_object_or_404(AdminProfile, pk=pk)
    serializer = StaffRoleAssignSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if serializer.validated_data['approved']:
        profile.staff_type = serializer.validated_data['staff_type']
        profile.is_approved = True
        profile.save(update_fields=['staff_type', 'is_approved'])
        record_activity(
            request.user,
            ActivityLog.CATEGORY_DECISION,
            'staff_role_assigned',
            f'{profile.name} was assigned the {profile.staff_type} role.',
            target=profile,
        )
        return Response({'detail': f'{profile.name} has been assigned as {profile.staff_type}.'})

    profile.user.is_active = False
    profile.user.save(update_fields=['is_active'])
    record_activity(
        request.user,
        ActivityLog.CATEGORY_DECISION,
        'staff_rejected',
        f'{profile.name} staff registration was rejected.',
        target=profile,
    )
    return Response({'detail': f'{profile.name}\u2019s registration has been rejected.'})
