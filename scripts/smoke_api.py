"""Exercise the local HTTP API without changing an existing watchlist."""

import argparse
import json
import math
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]


def check_concurrent_sign_in(origin, credentials):
    barrier = Barrier(2)

    def sign_in():
        with httpx.Client(base_url=origin, timeout=35, trust_env=False) as client:
            response = client.get('/api/v1/session/')
            response.raise_for_status()
            token = response.json()['csrf_token']
            barrier.wait(timeout=15)
            response = client.post('/api/v1/session/', json=credentials, headers={'X-CSRFToken': token})
            assert response.status_code == 200
            token = response.json()['csrf_token']
            assert client.delete('/api/v1/session/', headers={'X-CSRFToken': token}).status_code == 200
            return response.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(sign_in) for _ in range(2)]
        return [future.result(timeout=55) for future in futures]


def check_research(client, headers):
    datasets = client.get('/api/v1/research/datasets/').json()['items']
    dataset = next(item for item in datasets if item['name'] == 'Synthetic pipeline fixture')
    assert dataset['data_kind'] == 'synthetic_fixture'
    inputs = {'dataset_id': dataset['id'], 'horizon_sessions': 5, 'idempotency_key': str(uuid.uuid4())}
    response = client.post('/api/v1/research/runs/', json=inputs, headers=headers)
    assert response.status_code == 201
    run = response.json()
    result = run['result']
    assert result['dataset_version'] == dataset['version']
    assert result['empirical_performance_established'] is False
    assert result['evidence_kind'] == 'synthetic_pipeline_check'
    repeated = client.post('/api/v1/research/runs/', json=inputs, headers=headers)
    assert repeated.status_code == 200 and repeated.json() == run
    assert client.get('/api/v1/research/runs/' + run['id'] + '/').json() == run
    for score in result['evaluation']:
        assert all(math.isfinite(score[key]) for key in ('mae', 'rmse', 'return_mae', 'return_rmse', 'directional_accuracy'))
        assert sum(sum(row) for row in score['direction_confusion']) == score['n']
    assert all(len(method['points']) == 6 for method in result['forecast']['models'])
    return {
        'run_id': run['id'], 'dataset_version': dataset['version'], 'source_kind': dataset['data_kind'],
        'empirical_performance_established': False, 'horizon_sessions': 5,
        'evaluation_rows': len(result['evaluation_rows']), 'idempotent_replay': True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', default='http://127.0.0.1:8000')
    parser.add_argument('--include-research', action='store_true', help='Create and verify an explicit synthetic research run.')
    parser.add_argument('--concurrent-sign-in', action='store_true', help='Verify two synchronized sign-ins before the normal checks.')
    args = parser.parse_args()
    origin = args.origin
    parsed = urlparse(origin)
    if parsed.scheme not in {'http', 'https'} or parsed.hostname not in {'127.0.0.1', 'localhost', '::1'} or parsed.username or parsed.password or parsed.path not in {'', '/'} or parsed.query or parsed.fragment:
        parser.error('Smoke tests require an explicit loopback HTTP(S) origin without credentials or a path.')
    credentials = json.loads((ROOT / '.local/credentials.json').read_text())
    concurrent_sign_ins = check_concurrent_sign_in(origin, credentials) if args.concurrent_sign_in else None
    with httpx.Client(base_url=origin, timeout=20, trust_env=False) as client:
        assert client.get('/health/').json()['status'] == 'ok'
        assert client.get('/health/ready/').status_code == 200
        assert client.get('/api/v1/watchlist/').status_code == 403
        initial = client.get('/api/v1/session/').json()
        assert client.post('/api/v1/session/', json=credentials).status_code == 403
        authenticated = client.post('/api/v1/session/', json=credentials, headers={'X-CSRFToken': initial['csrf_token']})
        authenticated.raise_for_status()
        session = authenticated.json()
        assert session['authenticated']
        headers = {'X-CSRFToken': session['csrf_token']}
        search = client.get('/api/v1/instruments/', params={'query': 'apple'}).json()['items']
        assert search[0]['id'] == 'xnas-aapl'
        bars = client.get('/api/v1/instruments/xnas-aapl/bars/', params={'range': '1y', 'mode': 'demo'})
        bars.raise_for_status()
        payload = bars.json()
        assert payload['provenance']['data_mode'] == 'demo'
        assert payload['provenance']['as_of'] == payload['bars'][-1]['time']
        assert bars.headers['cache-control'] == 'private, no-store'
        original = {item['id'] for item in client.get('/api/v1/watchlist/').json()['items']}
        instrument_id = 'xnas-aapl'
        try:
            added = client.post('/api/v1/watchlist/', json={'instrument_id': instrument_id}, headers=headers)
            assert added.status_code in (200, 201)
            assert instrument_id in {item['id'] for item in client.get('/api/v1/watchlist/').json()['items']}
            assert client.post('/api/v1/watchlist/', json={'instrument_id': instrument_id}, headers={**headers, 'Origin': 'https://untrusted.invalid'}).status_code == 403
        finally:
            if instrument_id not in original:
                assert client.delete(f'/api/v1/watchlist/{instrument_id}/', headers=headers).status_code == 204
        assert {item['id'] for item in client.get('/api/v1/watchlist/').json()['items']} == original
        assert client.post('/api/rl/train/', json={}, headers=headers).status_code == 404
        if not session['market_data_enabled']:
            assert client.get('/api/v1/instruments/xnas-aapl/bars/?mode=market').status_code == 503
        research = check_research(client, headers) if args.include_research else None
        assert client.delete('/api/v1/session/', headers=headers).json()['authenticated'] is False
        if args.include_research:
            assert client.get('/api/v1/research/runs/').status_code == 403
    checks = ['health', 'readiness', 'anonymous denial', 'login CSRF', 'sign in', 'instrument search', 'daily demo provenance', 'private cache', 'watchlist persistence and restoration', 'hostile origin denial', 'legacy route exclusion', 'market mode gate', 'sign out']
    if args.include_research:
        checks.extend(['research synthetic provenance', 'research creation', 'research persisted replay', 'research metric consistency', 'research anonymous denial'])
    if args.concurrent_sign_in:
        checks.append('concurrent sign-in and logout')
    print(json.dumps({'result': 'PASS', 'origin': origin, 'checks': checks, 'visible_bars': len(payload['bars']), 'research': research, 'concurrent_sign_ins': concurrent_sign_ins}, indent=2))


if __name__ == '__main__':
    main()
