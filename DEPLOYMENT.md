# Production worker operations

The API queues submissions with status `pending`. A separate process must run
the grading worker so queued submissions are sent to Judge0.

## Recommended worker process

Run this as a long-lived process in the production service:

```text
python manage.py check_submissions --max-submissions 25 --poll-seconds 10
```

The worker claims each row inside a database transaction before calling Judge0,
so two worker processes will not claim the same pending submission when using
PostgreSQL. Keep one worker process per deployment unless additional capacity
is needed.

## Failure and retry behavior

- Judge0 failures are retried up to three worker attempts by default.
- After the final failed attempt, the submission is marked `failed` and the
  error is stored in `last_error`.
- Override the limit when necessary:

```text
python manage.py check_submissions --max-attempts 5 --poll-seconds 10
```

- Use the default zero polling interval for a one-shot scheduler invocation:

```text
python manage.py check_submissions --max-submissions 25
```

Students may submit a new attempt after a failed submission. A passed problem
remains complete and is not accepted again.

## Required environment

The worker uses the same environment as Django and requires:

- `SECRET_KEY`
- `DATABASE_URL` for production PostgreSQL/Supabase
- `JUDGE0_URL`
- `JUDGE0_AUTH_TOKEN` when the Judge0 instance requires it

Run migrations before starting the API or worker:

```text
python manage.py migrate
```
