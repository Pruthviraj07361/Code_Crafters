import os
from urllib.parse import urlparse

import requests


DEFAULT_LANGUAGE_IDS = {
    'c': 50,
    'cpp': 54,
    'go': 60,
    'java': 62,
    'javascript': 63,
    'python': 71,
    'rust': 73,
}


def get_judge0_config():
    api_key = os.environ.get('JUDGE0_API_KEY', '').strip()
    base_url = (
        os.environ.get('JUDGE0_BASE_URL')
        or os.environ.get('JUDGE0_URL')
        or ''
    ).strip()
    return {
        'api_key': api_key,
        'base_url': base_url,
    }


def _language_id(language):
    if language not in DEFAULT_LANGUAGE_IDS:
        raise ValueError(f'Automatic grading does not support {language}.')

    configured_id = os.environ.get(f'JUDGE0_LANGUAGE_ID_{language.upper()}')
    try:
        return int(configured_id) if configured_id else DEFAULT_LANGUAGE_IDS[language]
    except ValueError as exc:
        raise RuntimeError(f'Invalid Judge0 language ID for {language}.') from exc


def run_judge0_check(submission):
    config = get_judge0_config()
    if not config['base_url']:
        raise RuntimeError(
            'Judge0 is not configured. Set JUDGE0_BASE_URL or JUDGE0_URL.'
        )

    test_cases = submission.problem_statement.test_cases
    if not isinstance(test_cases, list) or not test_cases:
        raise ValueError('This problem has no grading test cases configured.')

    base_url = config['base_url'].rstrip('/')
    headers = {}
    if config['api_key']:
        headers['X-RapidAPI-Key'] = config['api_key']
        host = urlparse(base_url).hostname
        if host:
            headers['X-RapidAPI-Host'] = host

    for index, test_case in enumerate(test_cases, start=1):
        response = requests.post(
            f'{base_url}/submissions',
            params={'base64_encoded': 'false', 'wait': 'true'},
            headers=headers,
            json={
                'language_id': _language_id(submission.language),
                'source_code': submission.code,
                'stdin': test_case['input'],
                'expected_output': test_case['expected_output'],
            },
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(f'Judge0 returned HTTP {response.status_code}.')

        result = response.json()
        result_status = result.get('status') or {}
        status_description = result_status.get('description', 'Unknown status')
        if result_status.get('id') != 3:
            output = '\n'.join(
                value.strip()
                for value in (
                    status_description,
                    result.get('compile_output') or '',
                    result.get('stderr') or '',
                    result.get('stdout') or '',
                )
                if value and value.strip()
            )
            return False, f'Test case {index} failed: {output}'

    return True, f'All {len(test_cases)} test cases passed.'
