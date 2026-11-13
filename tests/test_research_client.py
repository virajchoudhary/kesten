import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "frontend/api_client.py"
spec = importlib.util.spec_from_file_location("research_api_client", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ResearchClientTests(unittest.TestCase):
    @patch.dict(os.environ, {"CADRISYN_LEGACY_API_URL": "http://127.0.0.1:8001/api", "CADRISYN_LEGACY_USERNAME": "test-operator", "CADRISYN_LEGACY_PASSWORD": "fixture-only-password"})
    @patch.object(module.http, "request")
    def test_staff_credentials_are_sent_only_to_exact_local_api(self, request):
        module.client.get("http://127.0.0.1:8001/api/hpo-status/")
        self.assertEqual(request.call_args.kwargs["auth"], ("test-operator", "fixture-only-password"))
        self.assertEqual(request.call_args.kwargs["timeout"], 30)
        self.assertEqual(request.call_args.kwargs["headers"]["X-Cadrisyn-Research"], "1")
        for url in ("https://example.com/api/", "http://127.0.0.1:8002/api/", "http://127.0.0.1:8001/api-elsewhere"):
            module.client.get(url)
            self.assertNotIn("auth", request.call_args.kwargs)
            self.assertNotIn("headers", request.call_args.kwargs)

    @patch.dict(os.environ, {"CADRISYN_LEGACY_API_URL": "https://external.example/api"})
    def test_nonlocal_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            module.client.get("https://external.example/api/status")


if __name__ == "__main__":
    unittest.main()
