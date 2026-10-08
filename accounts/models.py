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


class ActivityLog(models.Model):
    CATEGORY_ASSIGNMENT = 'assignment'
    CATEGORY_REVIEW = 'review'
    CATEGORY_MEETING = 'meeting'
    CATEGORY_DECISION = 'decision'
    CATEGORY_PROFILE = 'profile'
    CATEGORY_CHOICES = [
        (CATEGORY_ASSIGNMENT, 'Problem assignment'),
        (CATEGORY_REVIEW, 'Code review'),
        (CATEGORY_MEETING, 'Meeting'),
        (CATEGORY_DECISION, 'Approval decision'),
        (CATEGORY_PROFILE, 'Profile'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs',
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    action = models.CharField(max_length=80)
    description = models.TextField()
    target_type = models.CharField(max_length=80, blank=True)
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.description


def record_activity(actor, category, action, description, target=None):
    return ActivityLog.objects.create(
        actor=actor,
        category=category,
        action=action,
        description=description,
        target_type=target.__class__.__name__ if target is not None else '',
        target_id=getattr(target, 'pk', None),
    )
