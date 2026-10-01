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
    """The club's next meeting. Only one row is ever kept: the supervisor
    endpoint updates it in place instead of adding a new row each time."""

    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    scheduled_for = models.DateTimeField()
    updated_by = models.ForeignKey(
        'accounts.AdminProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='meetings_updated',
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
