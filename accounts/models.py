from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    """Extra fields collected at student registration, on top of the base
    Django User (username/email/password) that accounts.views.register creates."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile'
    )
    name = models.CharField(max_length=150)
    division = models.CharField(max_length=10)
    division_roll_number = models.CharField(max_length=20)
    branch = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    enrollment_number = models.CharField(max_length=50, unique=True)
    semester = models.PositiveSmallIntegerField(null=True, blank=True)
    # A faculty member must accept this student's registration before they
    # can sign in (see the faculty Approvals page in the PRD).
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class AdminProfile(models.Model):
    """Extra fields collected at admin registration. staff_type stays blank
    until a superuser assigns faculty/supervisor/superuser from Staff Management."""

    STAFF_FACULTY = 'faculty'
    STAFF_SUPERVISOR = 'supervisor'
    STAFF_SUPERUSER = 'superuser'
    STAFF_TYPE_CHOICES = [
        (STAFF_FACULTY, 'Faculty'),
        (STAFF_SUPERVISOR, 'Supervisor'),
        (STAFF_SUPERUSER, 'Superuser'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_profile'
    )
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPE_CHOICES, blank=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name
