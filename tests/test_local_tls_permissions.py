import csv
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts.ops import prepare_local_tls
from scripts.ops.prepare_local_tls import protect_directory


class LocalSecretPermissionsTests(unittest.TestCase):
    def test_acl_failure_stops_before_creating_tls_or_secret_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            local = root / '.local'
            local.mkdir(mode=0o700)
            destination = local / 'blocked-acl'
            identity = SimpleNamespace(returncode=0, stdout='DOMAIN\\user,S-1-5-21-123-456-789-1000\n', stderr='')
            denied = SimpleNamespace(returncode=1, stdout='', stderr='Access denied')
            run = Mock(side_effect=[identity, denied])
            with patch.object(prepare_local_tls, 'ROOT', root), \
                    patch.object(prepare_local_tls, 'os', SimpleNamespace(name='nt')), \
                    patch.object(prepare_local_tls, 'subprocess', SimpleNamespace(run=run)):
                with self.assertRaisesRegex(RuntimeError, 'restrict the new private directory'):
                    prepare_local_tls.prepare(destination, 'openssl', 'api-image', 'web-image')
            self.assertEqual(list(destination.iterdir()), [])
            self.assertEqual(run.call_count, 2)

    def test_invalid_windows_sid_stops_before_creating_any_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            local = root / '.local'
            local.mkdir(mode=0o700)
            destination = local / 'blocked'
            identity = SimpleNamespace(returncode=0, stdout='DOMAIN\\user,not-a-sid\n', stderr='')
            run = Mock(return_value=identity)
            with patch.object(prepare_local_tls, 'ROOT', root), \
                    patch.object(prepare_local_tls, 'os', SimpleNamespace(name='nt')), \
                    patch.object(prepare_local_tls, 'subprocess', SimpleNamespace(run=run)):
                with self.assertRaisesRegex(RuntimeError, 'valid Windows user SID'):
                    prepare_local_tls.prepare(destination, 'openssl', 'api-image', 'web-image')

            self.assertEqual(list(destination.iterdir()), [])
            self.assertEqual(run.call_count, 1)
            if os.name != 'nt':
                self.assertEqual(destination.stat().st_mode & 0o777, 0o700)

    def test_new_private_directory_restricts_access_and_keeps_files_readable(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'private'
            directory.mkdir()
            protect_directory(directory)
            secret = directory / 'test-key'
            secret.write_text('test fixture, not a credential')
            self.assertEqual(secret.read_text(), 'test fixture, not a credential')
            if os.name == 'nt':
                identity = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'], capture_output=True, text=True, check=True)
                sid = next(csv.reader(identity.stdout.splitlines()))[1]
                command = '(Get-Acl -LiteralPath $env:CADRISYN_ACL_TEST_PATH).Access | ForEach-Object { $_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value } | ConvertTo-Json -Compress'
                environment = {key: value for key, value in os.environ.items() if key.upper() != 'PSMODULEPATH'}
                environment['CADRISYN_ACL_TEST_PATH'] = str(secret)
                result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', command], env=environment, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(set(json.loads(result.stdout)), {sid, 'S-1-5-18'})
            else:
                self.assertEqual(directory.stat().st_mode & 0o777, 0o700)


if __name__ == '__main__':
    unittest.main()
