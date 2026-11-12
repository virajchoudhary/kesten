from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, connections
from django.test import RequestFactory, TransactionTestCase

from accounts.models import LoginAttemptState
from accounts.services import (
    LOGIN_FAILURE_LIMIT,
    InvalidAccountToken,
    accept_invitation,
    authenticate_login,
    confirm_password_reset,
    issue_invitation,
    issue_password_reset,
    login_identifier_digest,
)


@skipUnless(connection.vendor == "postgresql", "requires PostgreSQL row-level locking")
class PostgreSQLTokenConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        user_model = get_user_model()
        self.operator = user_model.objects.create_user(
            username="operator",
            password="operator-password-516!secure",
            is_staff=True,
        )
        self.user = user_model.objects.create_user(
            username="reset-target",
            password="the old password is strong 892!",
        )

    def _race(self, consume):
        start = Barrier(2)

        def worker():
            close_old_connections()
            try:
                start.wait(timeout=10)
                consume()
                return "consumed"
            except InvalidAccountToken:
                return "rejected"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(lambda _: worker(), range(2)))

    def test_invitation_token_is_consumed_by_only_one_concurrent_request(self):
        _, token = issue_invitation(username="concurrent-user", issued_by=self.operator)
        results = self._race(
            lambda: accept_invitation(
                token=token,
                password="a strong concurrent password 559!",
                confirmation="a strong concurrent password 559!",
            )
        )
        self.assertCountEqual(results, ["consumed", "rejected"])
        self.assertEqual(get_user_model().objects.filter(username="concurrent-user").count(), 1)

    def test_password_reset_token_is_consumed_by_only_one_concurrent_request(self):
        _, token = issue_password_reset(user=self.user, issued_by=self.operator)
        results = self._race(
            lambda: confirm_password_reset(
                token=token,
                password="a strong reset password 529!",
                confirmation="a strong reset password 529!",
            )
        )
        self.assertCountEqual(results, ["consumed", "rejected"])

    def test_concurrent_unknown_user_failures_are_serialized_and_capped(self):
        username = "concurrent-unregistered-user"
        start = Barrier(8)

        def worker():
            close_old_connections()
            try:
                request = RequestFactory().post(
                    "/api/v1/session/",
                    REMOTE_ADDR="127.0.0.1",
                )
                start.wait(timeout=10)
                return authenticate_login(
                    request,
                    username,
                    "incorrect password 991!",
                )
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: worker(), range(8)))

        self.assertEqual(results, [None] * 8)
        attempt = LoginAttemptState.objects.get(
            identifier_digest=login_identifier_digest(username, "127.0.0.1")
        )
        self.assertEqual(attempt.failure_count, LOGIN_FAILURE_LIMIT)
        self.assertIsNotNone(attempt.locked_until)
