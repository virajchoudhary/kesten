"""Run the existing quantitative API tests without provider/network access."""

import os
import runpy
import socket
import sys

from dev import ROOT, development_environment


def deny_network(*args, **kwargs):
    raise RuntimeError('Network access is disabled for the research regression suite.')


def main():
    environment = development_environment()
    environment.update({
        'DJANGO_SETTINGS_MODULE': 'quantvision.legacy_settings',
        'CADRISYN_LEGACY_ENABLED': 'true',
        'CADRISYN_DB_PATH': str(ROOT / '.local/research-test-unused.sqlite3'),
        'POLYGON_API_KEY': '',
        'GROQ_API_KEY': '',
        'HF_HUB_OFFLINE': '1',
        'TRANSFORMERS_OFFLINE': '1',
    })
    os.environ.update(environment)
    socket.socket.connect = deny_network
    socket.create_connection = deny_network
    os.chdir(ROOT / 'backend')
    sys.path.insert(0, str(ROOT / 'backend'))
    sys.argv = ['manage.py', 'test', 'api.tests', '--noinput', '--verbosity', '2']
    runpy.run_path('manage.py', run_name='__main__')


if __name__ == '__main__':
    main()
