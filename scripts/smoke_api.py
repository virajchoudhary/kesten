"""Exercise the local HTTP API without changing an existing watchlist."""

import json
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    origin = 'http://127.0.0.1:8000'
    assert urlparse(origin).hostname == '127.0.0.1'
    credentials = json.loads((ROOT / '.local/credentials.json').read_text())
    with httpx.Client(base_url=origin, timeout=20, trust_env=False) as client:
        assert client.get('/health/').json()['status'] == 'ok'
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
        assert client.delete('/api/v1/session/', headers=headers).json()['authenticated'] is False
    print(json.dumps({'result': 'PASS', 'checks': ['health', 'anonymous denial', 'login CSRF', 'sign in', 'instrument search', 'daily demo provenance', 'private cache', 'watchlist persistence and restoration', 'hostile origin denial', 'legacy route exclusion', 'market mode gate', 'sign out'], 'visible_bars': len(payload['bars'])}, indent=2))


if __name__ == '__main__':
    main()
