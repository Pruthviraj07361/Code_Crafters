from rest_framework.permissions import BasePermission

from .models import AdminProfile


def _staff_type(user):
    """Returns the requesting user's AdminProfile.staff_type, or None if
    they're unauthenticated, a student, or an admin with no role assigned
    yet."""
    if not user or not user.is_authenticated:
        return None
    admin_profile = getattr(user, 'admin_profile', None)
    if admin_profile is None or not admin_profile.is_approved:
        return None
    return admin_profile.staff_type or None


def _approved_student_profile(user):
    """Returns the requesting user's StudentProfile if they're authenticated
    and a faculty member has approved their registration, else None."""
    if not user or not user.is_authenticated:
        return None
    student_profile = getattr(user, 'student_profile', None)
    if student_profile is None or not student_profile.is_approved:
        return None
    return student_profile


class IsFaculty(BasePermission):
    message = 'Only faculty can access this endpoint.'

    def has_permission(self, request, view):
        return _staff_type(request.user) == AdminProfile.STAFF_FACULTY


class IsFacultyOrSuperuser(BasePermission):
    message = 'Only faculty or superusers can access this endpoint.'

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return _staff_type(request.user) in (
            AdminProfile.STAFF_FACULTY,
            AdminProfile.STAFF_SUPERUSER,
        )


class IsSupervisor(BasePermission):
    message = 'Only supervisors can access this endpoint.'

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return _staff_type(request.user) == AdminProfile.STAFF_SUPERVISOR


class CanViewStudentProgress(BasePermission):
    message = 'Only faculty, supervisors, or superusers can access this endpoint.'

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return _staff_type(request.user) in (
            AdminProfile.STAFF_FACULTY,
            AdminProfile.STAFF_SUPERVISOR,
            AdminProfile.STAFF_SUPERUSER,
        )


class IsSuperuser(BasePermission):
    message = 'Only a superuser can access this endpoint.'

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return _staff_type(request.user) == AdminProfile.STAFF_SUPERUSER


class IsApprovedStudent(BasePermission):
    message = 'Only approved students can access this endpoint.'

    def has_permission(self, request, view):
        return _approved_student_profile(request.user) is not None