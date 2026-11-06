"""Run workspace checks using an isolated development configuration."""

import subprocess
import sys

from dev import ROOT, development_environment


def main():
    environment = development_environment()
    environment['DJANGO_SETTINGS_MODULE'] = 'quantvision.settings'
    commands = [
        ['check'],
        ['makemigrations', '--check', '--dry-run'],
        ['test', 'workspace', 'api.test_security', '--noinput'],
    ]
    for arguments in commands:
        subprocess.run([sys.executable, 'manage.py', *arguments], cwd=ROOT / 'backend', env=environment, check=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/check_contract.py')], env=environment, check=True)
    environment.update({'DJANGO_DEBUG': 'false', 'DJANGO_ALLOWED_HOSTS': 'cadrisyn.invalid'})
    subprocess.run([sys.executable, 'manage.py', 'check', '--deploy', '--fail-level', 'ERROR'], cwd=ROOT / 'backend', env=environment, check=True)


if __name__ == '__main__':
    main()
