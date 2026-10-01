from django.db import models


class Submission(models.Model):
    LANGUAGE_C = 'c'
    LANGUAGE_HTML = 'html'
    STATUS_PENDING = 'pending'
    STATUS_CHECKING = 'checking'
    STATUS_SUBMITTED = 'submitted'
    STATUS_PASSED = 'passed'
    STATUS_FAILED = 'failed'

    LANGUAGE_CHOICES = [
        (LANGUAGE_C, 'C'),
        (LANGUAGE_HTML, 'HTML'),
    ]
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CHECKING, 'Checking'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_PASSED, 'Passed'),
        (STATUS_FAILED, 'Failed'),
    ]

    student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    problem_statement = models.ForeignKey(
        'assignments.ProblemStatement',
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    code = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    judge0_output = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(auto_now_add=True)
    checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at', '-id']

    def __str__(self):
        return f'{self.student.user.email} -> {self.problem_statement.title} ({self.language})'
