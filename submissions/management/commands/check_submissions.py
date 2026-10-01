from django.core.management.base import BaseCommand
from django.utils import timezone

from submissions.judge0 import run_judge0_check
from submissions.models import Submission


class Command(BaseCommand):
    help = (
        'Checks pending C submissions via Judge0. HTML submissions are marked as '
        'submitted without compile checking.'
    )

    def handle(self, *args, **options):
        pending = Submission.objects.filter(status=Submission.STATUS_PENDING).select_related(
            'problem_statement',
            'student',
            'student__user',
        )

        for submission in pending:
            if submission.language == Submission.LANGUAGE_HTML:
                submission.status = Submission.STATUS_SUBMITTED
                submission.checked_at = timezone.now()
                submission.save(update_fields=['status', 'checked_at'])
                continue

            submission.status = Submission.STATUS_CHECKING
            submission.save(update_fields=['status'])

            try:
                passed, judge0_output = run_judge0_check(submission)
            except Exception as exc:  # pragma: no cover - branch only exercised with a real API misconfig
                submission.status = Submission.STATUS_FAILED
                submission.judge0_output = str(exc)
                submission.checked_at = timezone.now()
                submission.save(update_fields=['status', 'judge0_output', 'checked_at'])
                raise

            submission.status = Submission.STATUS_PASSED if passed else Submission.STATUS_FAILED
            submission.judge0_output = judge0_output
            submission.checked_at = timezone.now()
            submission.save(update_fields=['status', 'judge0_output', 'checked_at'])

            self.stdout.write(
                self.style.SUCCESS(
                    f'Checked submission #{submission.pk}: {submission.status}'
                )
            )
