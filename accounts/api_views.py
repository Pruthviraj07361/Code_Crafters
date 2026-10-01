from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import AdminProfile, StudentProfile
from .permissions import IsFaculty, IsSuperuser
from .serializers import (
    AdminRegisterSerializer,
    LoginSerializer,
    PendingStaffSerializer,
    PendingStudentSerializer,
    StaffRoleAssignSerializer,
    StudentApprovalActionSerializer,
    StudentRegisterSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_student(request):
    serializer = StudentRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
        {'detail': 'Registration received, pending faculty approval.'},
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def register_admin(request):
    serializer = AdminRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
        {'detail': 'Registration received, pending role assignment by a superuser.'},
        status=status.HTTP_201_CREATED,
    )


def _serialize_user(user):
    """Build the {user: {...}} payload the frontend uses to decide which
    role's routes/pages to show. `role` is one of:
    'student', 'faculty', 'supervisor', 'superuser'."""
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
    user = authenticate(
        request,
        username=serializer.validated_data['email'],
        password=serializer.validated_data['password'],
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

    if student_profile is not None:
        if not student_profile.is_approved:
            return Response(
                {'detail': 'Your registration is pending faculty approval.'},
                status=status.HTTP_403_FORBIDDEN,
            )
    elif admin_profile is not None:
        if not admin_profile.is_approved or not admin_profile.staff_type:
            return Response(
                {'detail': 'Your registration is pending role assignment by a superuser.'},
                status=status.HTTP_403_FORBIDDEN,
            )
    else:
        # Shouldn't happen via the two register endpoints above, but covers
        # e.g. accounts created directly in Django admin without a profile.
        return Response(
            {'detail': 'No student or admin profile is linked to this account.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': _serialize_user(user)})


@api_view(['GET'])
@permission_classes([IsFaculty])
def pending_students(request):
    queryset = StudentProfile.objects.filter(is_approved=False).select_related('user')
    serializer = PendingStudentSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsFaculty])
def approve_student(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    serializer = StudentApprovalActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if serializer.validated_data['approved']:
        profile.is_approved = True
        profile.save(update_fields=['is_approved'])
        return Response({'detail': f'{profile.name} has been approved.'})

    # Rejected: deactivate the account rather than deleting it, so the
    # registration data isn't lost and a faculty member can revisit it.
    profile.user.is_active = False
    profile.user.save(update_fields=['is_active'])
    return Response({'detail': f'{profile.name}\u2019s registration has been rejected.'})


@api_view(['GET'])
@permission_classes([IsSuperuser])
def pending_staff(request):
    queryset = AdminProfile.objects.filter(staff_type='').select_related('user')
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
        return Response({'detail': f'{profile.name} has been assigned as {profile.staff_type}.'})

    profile.user.is_active = False
    profile.user.save(update_fields=['is_active'])
    return Response({'detail': f'{profile.name}\u2019s registration has been rejected.'})
