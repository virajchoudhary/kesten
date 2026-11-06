from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import TestCase


class HealthSessionIsolationTests(TestCase):
    def test_liveness_does_not_load_a_cookie_session_during_database_failure(self):
        user = get_user_model().objects.create_user("health-session-probe")
        self.client.force_login(user)
        with patch("django.contrib.sessions.backends.db.SessionStore.load", side_effect=OperationalError("database unavailable")) as load:
            response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        load.assert_not_called()
