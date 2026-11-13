"""Prepare a new, isolated loopback TLS rehearsal; never provision production trust."""

import argparse
import csv
import os
import re
import secrets
import subprocess
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[2]


def protect_directory(destination):
    if os.name == 'nt':
        identity = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'], capture_output=True, text=True, check=True)
        rows = list(csv.reader(identity.stdout.splitlines()))
        if len(rows) != 1 or len(rows[0]) != 2:
            raise RuntimeError('Could not determine a valid Windows user SID; refusing to prepare TLS files.')
        sid = rows[0][1].strip()
        if re.fullmatch(r'S-[0-9]+(?:-[0-9]+)+', sid, flags=re.ASCII) is None:
            raise RuntimeError('Could not determine a valid Windows user SID; refusing to prepare TLS files.')
        result = subprocess.run(['icacls', str(destination), '/inheritance:r', '/grant:r', '*' + sid + ':(OI)(CI)F', '*S-1-5-18:(OI)(CI)F'], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError('Could not restrict the new private directory to its creator and SYSTEM.')
    else:
        destination.chmod(0o700)


def prepare(destination, openssl, api_image, web_image):
    destination = destination.resolve()
    if not destination.is_relative_to(ROOT / '.local'):
        raise ValueError('Local rehearsal files must be inside this repository .local directory.')
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    protect_directory(destination)
    config = destination / 'openssl.cnf'
    config.write_text('[req]\ndistinguished_name=dn\n[dn]\n', encoding='ascii')

    def run(*arguments):
        result = subprocess.run([openssl, *arguments], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError('OpenSSL local certificate generation failed; partial files were retained.')

    run('req', '-config', str(config), '-x509', '-newkey', 'rsa:2048', '-sha256', '-days', '7', '-nodes',
        '-keyout', str(destination / 'ca.key'), '-out', str(destination / 'tls_ca'),
        '-subj', '/CN=Cadrisyn local rehearsal CA', '-addext', 'basicConstraints=critical,CA:TRUE')
    for service, san in [('gateway', 'DNS:localhost,IP:127.0.0.1'), ('database', 'DNS:database'), ('cache', 'DNS:cache')]:
        extension = destination / (service + '.ext')
        extension.write_text('subjectAltName=' + san + '\nextendedKeyUsage=serverAuth\nbasicConstraints=critical,CA:FALSE\n', encoding='ascii')
        run('req', '-config', str(config), '-new', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(destination / (service + '_key')),
            '-out', str(destination / (service + '.csr')), '-subj', '/CN=' + ('localhost' if service == 'gateway' else service))
        run('x509', '-req', '-sha256', '-days', '7', '-in', str(destination / (service + '.csr')), '-CA', str(destination / 'tls_ca'),
            '-CAkey', str(destination / 'ca.key'), '-set_serial', str(secrets.randbits(128)), '-extfile', str(extension), '-out', str(destination / (service + '_cert')))
        if os.name != 'nt':
            (destination / (service + '_key')).chmod(0o444)

    values = {key: secrets.token_urlsafe(48) for key in ['django_secret', 'admin_password', 'runtime_password', 'migration_password', 'cache_password']}
    values.update({
        'database_url': 'postgresql://cadrisyn:' + quote(values['runtime_password']) + '@database:5432/cadrisyn?sslmode=verify-full&sslrootcert=/run/secrets/tls_ca',
        'migration_url': 'postgresql://cadrisyn_migrator:' + quote(values['migration_password']) + '@database:5432/cadrisyn?sslmode=verify-full&sslrootcert=/run/secrets/tls_ca',
        'cache_url': 'rediss://:' + quote(values['cache_password']) + '@cache:6379/1?ssl_ca_certs=/run/secrets/tls_ca',
        'redis_config': 'port 0\ntls-port 6379\ntls-cert-file /run/secrets/cache_cert\ntls-key-file /run/secrets/cache_key\ntls-ca-cert-file /run/secrets/tls_ca\ntls-auth-clients no\nrequirepass ' + values['cache_password'] + '\nmaxmemory 128mb\nmaxmemory-policy noeviction\nsave ""\nappendonly no\n',
    })
    for name, value in values.items():
        with (destination / name).open('x', encoding='utf-8') as output:
            output.write(value)
    environment = {
        'CADRISYN_RELEASE_PROFILE': 'demo', 'CADRISYN_WEB_RELEASE_PROFILE': 'demo',
        'DJANGO_ALLOWED_HOSTS': 'localhost,127.0.0.1', 'DJANGO_CSRF_TRUSTED_ORIGINS': 'https://localhost:8443,https://127.0.0.1:8443',
        'CADRISYN_SECRET_DIR': destination.as_posix(), 'API_IMAGE': api_image, 'WEB_IMAGE': web_image,
        'DJANGO_DEBUG': 'false', 'DJANGO_TRUST_X_FORWARDED_PROTO': 'true',
        'DJANGO_SECRET_KEY_FILE': '/run/secrets/django_secret', 'DATABASE_URL_FILE': '/run/secrets/database_url', 'DJANGO_CACHE_URL_FILE': '/run/secrets/cache_url',
    }
    with (destination / 'rehearsal.env').open('x', encoding='utf-8') as output:
        output.write(''.join(key + '=' + value + '\n' for key, value in environment.items()))
    print('Prepared a new loopback-only demo rehearsal. Certificates expire in seven days; no trust store was modified.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--openssl', default='openssl')
    parser.add_argument('--api-image', required=True)
    parser.add_argument('--web-image', required=True)
    args = parser.parse_args()
    prepare(args.directory, args.openssl, args.api_image, args.web_image)


if __name__ == '__main__':
    main()
