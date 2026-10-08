from django.core.management.base import BaseCommand
from django.utils import timezone

from submissions.judge0 import run_judge0_check
from submissions.models import Submission


class Command(BaseCommand):
    help = (
        'Checks queued submissions via Judge0. Run this command from a scheduler or worker.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--max-submissions', type=int, default=25)

    def handle(self, *args, **options):
        pending = Submission.objects.filter(status=Submission.STATUS_PENDING).select_related(
            'problem_statement',
            'student',
            'student__user',
        )

        for submission in pending[:options['max_submissions']]:
            if submission.language == Submission.LANGUAGE_HTML:
                submission.status = Submission.STATUS_SUBMITTED
                submission.checked_at = timezone.now()
                submission.last_error = ''
                submission.save(update_fields=['status', 'checked_at', 'last_error'])
                continue

            submission.status = Submission.STATUS_CHECKING
            submission.attempt_count += 1
            submission.last_error = ''
            submission.save(update_fields=['status', 'attempt_count', 'last_error'])

            try:
                passed, judge0_output = run_judge0_check(submission)
            except Exception as exc:  # pragma: no cover - branch only exercised with a real API misconfig
                submission.status = Submission.STATUS_PENDING
                submission.last_error = str(exc)
                submission.judge0_output = ''
                submission.save(update_fields=['status', 'last_error', 'judge0_output'])
                self.stderr.write(
                    self.style.ERROR(f'Could not check submission #{submission.pk}: {exc}')
                )
                continue

            submission.status = Submission.STATUS_PASSED if passed else Submission.STATUS_FAILED
            submission.judge0_output = judge0_output
            submission.last_error = ''
            submission.checked_at = timezone.now()
            submission.save(update_fields=['status', 'judge0_output', 'last_error', 'checked_at'])

            self.stdout.write(
                self.style.SUCCESS(
                    f'Checked submission #{submission.pk}: {submission.status}'
                )
            )
