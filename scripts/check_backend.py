"""Run workspace checks using an isolated development configuration."""

import subprocess
import sys
from urllib.parse import quote

import certifi

from dev import ROOT, development_environment


def main():
    environment = development_environment()
    environment['DJANGO_SETTINGS_MODULE'] = 'quantvision.settings'
    commands = [
        ['check'],
        ['makemigrations', '--check', '--dry-run'],
        ['test', 'workspace', 'accounts', 'research', 'api.test_security', '--noinput'],
    ]
    for arguments in commands:
        subprocess.run([sys.executable, 'manage.py', *arguments], cwd=ROOT / 'backend', env=environment, check=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/check_contract.py')], env=environment, check=True)
    environment.update({
        'DJANGO_DEBUG': 'false',
        'CADRISYN_RELEASE_PROFILE': 'demo',
        'DJANGO_ALLOWED_HOSTS': 'cadrisyn.invalid',
        'DJANGO_CSRF_TRUSTED_ORIGINS': 'https://cadrisyn.invalid',
        'DATABASE_URL': 'postgresql://configuration-probe:fixture@database.invalid/cadrisyn?sslmode=verify-full&sslrootcert=' + quote(certifi.where()),
        'DJANGO_CACHE_URL': 'rediss://:fixture@cache.invalid:6379/0?ssl_ca_certs=' + quote(certifi.where()),
    })
    subprocess.run([sys.executable, 'manage.py', 'check', '--deploy', '--fail-level', 'ERROR'], cwd=ROOT / 'backend', env=environment, check=True)


if __name__ == '__main__':
    main()
