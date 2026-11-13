"""Read-only configuration and HTTPS readiness checks; never deploy or migrate."""
import argparse
import json
import os
import re
import ssl
import sys
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import dotenv_values


def inspect_configuration(environment):
    checks = []

    def check(name, passed):
        checks.append({'check': name, 'status': 'PASS' if passed else 'FAIL'})

    def secret(name):
        plain = environment.get(name, '').strip()
        filename = environment.get(name + '_FILE', '').strip()
        check(name.lower() + '_file_injection', bool(filename) and not plain)
        try:
            raw = Path(filename).read_bytes() if filename else b''
            return raw.decode().rstrip('\r\n') if 1 <= len(raw) <= 65536 else ''
        except (OSError, UnicodeDecodeError):
            return ''

    check('non_debug', environment.get('DJANGO_DEBUG', '').lower() in {'false', '0', 'off', 'no'})
    profile = environment.get('CADRISYN_RELEASE_PROFILE')
    check('release_profile', profile in {'demo', 'historical_research'})
    check('matching_web_profile', environment.get('CADRISYN_WEB_RELEASE_PROFILE') == profile)
    hosts = [host.strip() for host in environment.get('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]
    check('explicit_hosts', bool(hosts) and all(re.fullmatch(r'[A-Za-z0-9.-]+', host) and '*' not in host and not host.startswith('.') for host in hosts))
    origins = [origin.strip() for origin in environment.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]
    check('https_csrf_origins', bool(origins) and all(urlparse(origin).scheme == 'https' and urlparse(origin).hostname in hosts and origin == 'https://' + urlparse(origin).netloc and not urlparse(origin).username for origin in origins))
    check('same_origin_cors', not environment.get('DJANGO_CORS_ALLOWED_ORIGINS', '').strip())
    check('https_redirect', environment.get('DJANGO_SECURE_SSL_REDIRECT', 'true').lower() == 'true')
    check('trusted_gateway_proto', environment.get('DJANGO_TRUST_X_FORWARDED_PROTO', '').lower() == 'true')
    for feature in ['CADRISYN_LEGACY_ENABLED', 'CADRISYN_MARKET_DATA_ENABLED', 'CADRISYN_ADMIN_ENABLED', 'CADRISYN_LEGACY_SCHEDULER_ENABLED']:
        check(feature.lower(), environment.get(feature, 'false').lower() == 'false')
    check('django_secret_length', len(secret('DJANGO_SECRET_KEY')) >= 50)
    for name, value, schemes in [('database', secret('DATABASE_URL'), {'postgres', 'postgresql'}), ('cache', secret('DJANGO_CACHE_URL'), {'rediss'})]:
        try:
            parsed = urlparse(value)
            query = parse_qs(parsed.query)
            if name == 'database':
                valid = parsed.scheme in schemes and parsed.username == 'cadrisyn' and bool(parsed.password) and query.get('sslmode') == ['verify-full'] and Path(query.get('sslrootcert', [''])[0]).is_file()
            else:
                valid = parsed.scheme in schemes and bool(parsed.password) and Path(query.get('ssl_ca_certs', [''])[0]).is_file() and query.get('ssl_cert_reqs', ['required']) == ['required'] and query.get('ssl_check_hostname', ['true']) == ['true']
            check(name + '_authenticated_verified_tls', valid and bool(parsed.hostname))
        except ValueError:
            check(name + '_authenticated_verified_tls', False)
    for name in ['API_IMAGE', 'WEB_IMAGE']:
        check(name.lower() + '_immutable', bool(re.fullmatch(r'(?:[^\s]+@)?sha256:[0-9a-f]{64}', environment.get(name, ''))))
    return {'result': 'PASS' if all(row['status'] == 'PASS' for row in checks) else 'FAIL', 'profile': profile, 'checks': checks, 'scope': 'Configuration only; does not establish hosted CI, data rights, off-host recovery or production deployment readiness.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    configuration = parser.add_mutually_exclusive_group(required=True)
    configuration.add_argument('--env-file', type=Path)
    configuration.add_argument('--environment', action='store_true', help='Inspect this process environment, including container secret paths.')
    parser.add_argument('--origin')
    parser.add_argument('--ca', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        environment = dict(os.environ) if args.environment else {key: value for key, value in dotenv_values(args.env_file, interpolate=False).items() if value is not None}
        result = inspect_configuration(environment)
        if args.origin:
            parsed = urlparse(args.origin)
            if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.path not in {'', '/'} or parsed.query or parsed.fragment:
                raise ValueError
            context = ssl.create_default_context(cafile=str(args.ca) if args.ca else None)
            with urllib.request.urlopen(args.origin.rstrip('/') + '/health/ready/', context=context, timeout=10) as response:
                ready = response.status == 200 and json.load(response).get('status') == 'ready'
            result['checks'].append({'check': 'https_readiness', 'status': 'PASS' if ready else 'FAIL'})
            if not ready:
                result['result'] = 'FAIL'
            with urllib.request.urlopen(args.origin.rstrip('/') + '/health/release/', context=context, timeout=10) as response:
                actual = json.load(response)
            policy_matches = actual.get('profile') == result['profile'] and actual.get('debug') is False and actual.get('market_data_enabled') is False and actual.get('private_research_enabled') is (result['profile'] != 'demo')
            result['checks'].append({'check': 'live_release_policy', 'status': 'PASS' if policy_matches else 'FAIL'})
            if not policy_matches:
                result['result'] = 'FAIL'
        content = json.dumps(result, indent=2) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8') as output:
                output.write(content)
        print(content, end='')
        return 0 if result['result'] == 'PASS' else 1
    except (OSError, ValueError):
        print(json.dumps({'result': 'FAIL', 'error': 'Preflight configuration or HTTPS check could not be completed.'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
