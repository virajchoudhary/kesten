"""Regenerate the API schema and reject uncommitted contract drift."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from dev import ROOT, development_environment


def main():
    environment = development_environment()
    environment['DJANGO_SETTINGS_MODULE'] = 'quantvision.settings'
    with tempfile.TemporaryDirectory(dir=ROOT / '.local') as directory:
        generated = Path(directory) / 'openapi.json'
        subprocess.run([sys.executable, 'manage.py', 'spectacular', '--file', str(generated), '--format', 'openapi-json', '--validate', '--fail-on-warn'], cwd=ROOT / 'backend', env=environment, check=True)
        expected = json.loads((ROOT / 'contracts/openapi.json').read_text(encoding='utf-8'))
        actual = json.loads(generated.read_text(encoding='utf-8'))
        if expected != actual:
            raise SystemExit('API schema drift. Regenerate contracts/openapi.json and web API types together.')
    print('API schema matches contracts/openapi.json.')


if __name__ == '__main__':
    main()
