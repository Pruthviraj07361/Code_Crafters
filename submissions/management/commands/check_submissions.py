import time

from django.db import transaction
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
        parser.add_argument(
            '--max-attempts',
            type=int,
            default=3,
            help='Maximum Judge0 attempts before a worker error becomes failed.',
        )
        parser.add_argument(
            '--poll-seconds',
            type=int,
            default=0,
            help='Keep polling at this interval. Zero processes one batch and exits.',
        )

    def handle(self, *args, **options):
        if options['max_attempts'] < 1:
            raise self.CommandError('--max-attempts must be at least 1.')
        if options['poll_seconds'] < 0:
            raise self.CommandError('--poll-seconds cannot be negative.')

        while True:
            processed = self.process_batch(options)
            if options['poll_seconds'] == 0:
                return
            if processed == 0:
                time.sleep(options['poll_seconds'])

    def process_batch(self, options):
        processed = 0
        claimed_ids = set()
        for _ in range(options['max_submissions']):
            submission = self.claim_next_submission(claimed_ids)
            if submission is None:
                break
            processed += 1
            claimed_ids.add(submission.pk)
            if submission.language == Submission.LANGUAGE_HTML:
                submission.status = Submission.STATUS_SUBMITTED
                submission.checked_at = timezone.now()
                submission.last_error = ''
                submission.save(update_fields=['status', 'checked_at', 'last_error'])
                continue

            submission.status = Submission.STATUS_CHECKING
            submission.last_error = ''
            submission.save(update_fields=['status', 'last_error'])

            try:
                passed, judge0_output = run_judge0_check(submission)
            except Exception as exc:  # pragma: no cover - branch only exercised with a real API misconfig
                exhausted = submission.attempt_count >= options['max_attempts']
                submission.status = (
                    Submission.STATUS_FAILED
                    if exhausted
                    else Submission.STATUS_PENDING
                )
                submission.last_error = str(exc)
                submission.judge0_output = ''
                update_fields = ['status', 'last_error', 'judge0_output']
                if exhausted:
                    submission.checked_at = timezone.now()
                    update_fields.append('checked_at')
                submission.save(update_fields=update_fields)
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
        return processed

    @staticmethod
    def claim_next_submission(exclude_ids=None):
        with transaction.atomic():
            pending = (
                Submission.objects.select_for_update()
                .filter(status=Submission.STATUS_PENDING)
            )
            if exclude_ids:
                pending = pending.exclude(pk__in=exclude_ids)
            submission = pending.order_by('submitted_at', 'id').first()
            if submission is None:
                return None
            submission.status = Submission.STATUS_CHECKING
            submission.attempt_count += 1
            submission.last_error = ''
            submission.save(update_fields=['status', 'attempt_count', 'last_error'])
            return (
                Submission.objects.select_related(
                    'problem_statement',
                    'student',
                    'student__user',
                )
                .get(pk=submission.pk)
            )
