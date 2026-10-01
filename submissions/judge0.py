"""Judge0 integration facade.

The real HTTP client will be added once the project has the Judge0 API key and
host configuration from the user. This stub keeps the application and tests
structured without hardcoding a specific public API assumption.
"""

import os


def get_judge0_config():
    api_key = os.environ.get('JUDGE0_API_KEY', '').strip()
    base_url = os.environ.get('JUDGE0_BASE_URL', '').strip()
    return {
        'api_key': api_key,
        'base_url': base_url,
    }


def run_judge0_check(submission):
    """Placeholder for the real Judge0 HTTP call.

    The management command will call this helper, and tests will patch it to
    simulate the remote API response without hitting the real network.
    """
    config = get_judge0_config()
    if not config['api_key'] or not config['base_url']:
        raise RuntimeError(
            'Judge0 is not configured yet. Set JUDGE0_API_KEY and JUDGE0_BASE_URL '
            'before enabling the real check client.'
        )

    raise NotImplementedError(
        'Real Judge0 HTTP client not implemented yet. Add the API key and endpoint '
        'details before filling in the actual request logic.'
    )
