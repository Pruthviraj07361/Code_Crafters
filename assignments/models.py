from django.db import models


class ProblemStatement(models.Model):
    """A coding problem posted by a supervisor for students to solve."""

    title = models.CharField(max_length=200)
    description = models.TextField()
    # Input fed to the student's program when their submission is checked
    # (checking itself comes later, with the Submission model + Judge0).
    sample_input = models.TextField(blank=True)
    test_cases = models.JSONField(default=list, blank=True)
    week_number = models.PositiveSmallIntegerField(null=True, blank=True)
    # SET_NULL so problems survive if the supervisor's account is removed.
    created_by = models.ForeignKey(
        'accounts.AdminProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='problem_statements',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.title


class Meeting(models.Model):
    """An offline club meeting. Slot 1 and slot 2 support the PRD's two
    offline meetings while the legacy endpoint continues updating slot 1."""

    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    scheduled_for = models.DateTimeField()
    slot = models.PositiveSmallIntegerField(default=1)
    updated_by = models.ForeignKey(
        'accounts.AdminProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='meetings_updated',
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_by = models.ForeignKey(
        'accounts.AdminProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.title
