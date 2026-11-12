from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError
from django.test import Client, RequestFactory, TestCase
from django.utils import timezone

from accounts.constants import SESSION_EPOCH_SESSION_KEY
from accounts.models import (
    AccountInvitation,
    AccountSecurityState,
    LoginAttemptState,
    PasswordResetToken,
)
from accounts.services import (
    LOGIN_ATTEMPT_WINDOW,
    LOGIN_COOLDOWN,
    LOGIN_FAILURE_LIMIT,
    InvalidAccountToken,
    LoginInvalidated,
    accept_invitation,
    authenticate_login,
    bind_session,
    confirm_password_reset,
    digest_token,
    issue_invitation,
    issue_password_reset,
    login_identifier_digest,
)


class AccountsAPITests(TestCase):
    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.operator = user_model.objects.create_user(
            username="operator",
            password="operator-password-516!secure",
            is_staff=True,
        )
        self.client = Client(enforce_csrf_checks=True)

    def csrf(self, client=None):
        target = client or self.client
        return target.get("/api/v1/session/").json()["csrf_token"]

    def post_json(self, client, url, data):
        return client.post(
            url,
            data,
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf(client),
        )

    def assert_generic_login_failure(self, response):
        payload = response.json()
        payload.pop("request_id", None)
        self.assertEqual(
            payload,
            {
                "code": "invalid_credentials",
                "message": "The username or password is incorrect.",
                "field_errors": {},
            },
        )

    def login_client(
        self,
        client,
        username,
        password,
        *,
        remote_addr="127.0.0.1",
        forwarded_for=None,
    ):
        csrf_token = self.csrf(client)
        headers = {"REMOTE_ADDR": remote_addr}
        if forwarded_for is not None:
            headers["HTTP_X_FORWARDED_FOR"] = forwarded_for
        return client.post(
            "/api/v1/session/",
            {"username": username, "password": password},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
            **headers,
        )

    def issue_invite(self, username="analyst"):
        invitation, token = issue_invitation(username=username, issued_by=self.operator)
        self.assertEqual(invitation.token_digest, digest_token(token))
        self.assertNotEqual(invitation.token_digest, token)
        return invitation, token

    def test_invitation_mutation_requires_csrf_and_consumes_token_once(self):
        _, token = self.issue_invite()
        url = "/api/v1/account/invitations/accept/"
        payload = {
            "token": token,
            "new_password": "a strong account password 592!",
            "confirm_password": "a strong account password 592!",
        }
        self.assertEqual(self.client.post(url, payload, content_type="application/json").status_code, 403)

        response = self.post_json(self.client, url, payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"created": True})
        user = get_user_model().objects.get(username="analyst")
        self.assertTrue(user.check_password(payload["new_password"]))
        self.assertTrue(AccountSecurityState.objects.filter(user=user, session_epoch=0).exists())
        self.assertIsNotNone(AccountInvitation.objects.get().consumed_at)

        replay = self.post_json(self.client, url, payload)
        self.assertEqual(replay.status_code, 400)
        self.assertEqual(replay.json()["code"], "invalid_invitation")
        self.assertEqual(get_user_model().objects.filter(username="analyst").count(), 1)

    def test_invitation_is_expired_and_invalid_errors_do_not_identify_accounts(self):
        invitation, token = self.issue_invite()
        AccountInvitation.objects.filter(pk=invitation.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        url = "/api/v1/account/invitations/accept/"
        payload = {
            "token": token,
            "new_password": "another strong account password 592!",
            "confirm_password": "another strong account password 592!",
        }
        response = self.post_json(self.client, url, payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_invitation")
        self.assertEqual(response.json()["message"], "This invitation is invalid or expired.")
        self.assertFalse(get_user_model().objects.filter(username="analyst").exists())

    def test_invitation_password_policy_is_enforced_and_invalid_password_does_not_consume_token(self):
        _, token = self.issue_invite()
        url = "/api/v1/account/invitations/accept/"
        payload = {
            "token": token,
            "new_password": "password123",
            "confirm_password": "password123",
        }
        response = self.post_json(self.client, url, payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "password_policy")
        self.assertIsNone(AccountInvitation.objects.get().consumed_at)

    def test_invalid_invitation_does_not_reveal_reserved_username(self):
        response = self.post_json(
            self.client,
            "/api/v1/account/invitations/accept/",
            {
                "token": "x" * 43,
                "new_password": "a strong account password 592!",
                "confirm_password": "a strong account password 592!",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_invitation")
        self.assertNotIn("analyst", response.content.decode())

    def test_public_account_mutations_require_csrf(self):
        invite, token = self.issue_invite()
        reset_target = get_user_model().objects.create_user(
            username="reset-target",
            password="the old password is strong 892!",
        )
        reset, reset_token = issue_password_reset(user=reset_target, issued_by=self.operator)

        for url, payload in (
            (
                "/api/v1/account/invitations/accept/",
                {
                    "token": token,
                    "new_password": "a strong account password 592!",
                    "confirm_password": "a strong account password 592!",
                },
            ),
            (
                "/api/v1/account/password-reset/confirm/",
                {
                    "token": reset_token,
                    "new_password": "a different strong password 827!",
                    "confirm_password": "a different strong password 827!",
                },
            ),
        ):
            with self.subTest(url=url):
                response = self.client.post(url, payload, content_type="application/json")
                self.assertEqual(response.status_code, 403)

        self.assertIsNone(invite.consumed_at)
        self.assertIsNone(reset.consumed_at)

    def test_password_reset_revokes_sessions_and_can_only_be_consumed_once(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="reset-target",
            password="the old password is strong 892!",
        )
        state = AccountSecurityState.objects.create(user=user)
        old_client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.login_client(old_client, user.username, "the old password is strong 892!").status_code, 200)
        reset, token = issue_password_reset(user=user, issued_by=self.operator)
        payload = {
            "token": token,
            "new_password": "a different strong password 827!",
            "confirm_password": "a different strong password 827!",
        }

        response = self.post_json(
            self.client,
            "/api/v1/account/password-reset/confirm/",
            payload,
        )
        self.assertEqual(response.status_code, 200)
        state.refresh_from_db()
        self.assertEqual(state.session_epoch, 1)
        self.assertIsNotNone(PasswordResetToken.objects.get(pk=reset.pk).consumed_at)
        self.assertEqual(old_client.get("/api/v1/watchlist/").status_code, 403)
        self.assertTrue(user_model.objects.get(pk=user.pk).check_password(payload["new_password"]))

        replay = self.post_json(
            self.client,
            "/api/v1/account/password-reset/confirm/",
            payload,
        )
        self.assertEqual(replay.status_code, 400)
        self.assertEqual(replay.json()["code"], "invalid_reset_token")

    def test_invalid_reset_tokens_have_one_generic_public_response(self):
        response = self.post_json(
            self.client,
            "/api/v1/account/password-reset/confirm/",
            {
                "token": "x" * 43,
                "new_password": "a different strong password 827!",
                "confirm_password": "a different strong password 827!",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_reset_token")
        self.assertEqual(response.json()["message"], "This reset token is invalid or expired.")

    def test_change_password_preserves_current_session_and_invalidates_others(self):
        user_model = get_user_model()
        old_password = "existing strong password 647!"
        new_password = "replacement strong password 843!"
        user = user_model.objects.create_user(username="analyst", password=old_password)
        AccountSecurityState.objects.create(user=user)
        current_client = Client(enforce_csrf_checks=True)
        other_client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.login_client(current_client, "analyst", old_password).status_code, 200)
        self.assertEqual(self.login_client(other_client, "analyst", old_password).status_code, 200)
        old_session_key = current_client.session.session_key

        response = self.post_json(
            current_client,
            "/api/v1/account/password/change/",
            {
                "current_password": old_password,
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(current_client.session.session_key, old_session_key)
        self.assertEqual(current_client.get("/api/v1/watchlist/").status_code, 200)
        self.assertEqual(other_client.get("/api/v1/watchlist/").status_code, 403)
        self.assertTrue(user_model.objects.get(pk=user.pk).check_password(new_password))
        self.assertEqual(
            current_client.session[SESSION_EPOCH_SESSION_KEY],
            AccountSecurityState.objects.get(user=user).session_epoch,
        )

    def test_change_password_rejects_wrong_current_password(self):
        user = get_user_model().objects.create_user(
            username="analyst",
            password="existing strong password 647!",
        )
        AccountSecurityState.objects.create(user=user)
        self.assertEqual(
            self.login_client(self.client, "analyst", "existing strong password 647!").status_code,
            200,
        )
        response = self.post_json(
            self.client,
            "/api/v1/account/password/change/",
            {
                "current_password": "wrong password 647!",
                "new_password": "replacement strong password 843!",
                "confirm_password": "replacement strong password 843!",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_current_password")
        self.assertTrue(user.check_password("existing strong password 647!"))

    def test_revoke_sessions_supports_current_session_or_all_sessions(self):
        user = get_user_model().objects.create_user(
            username="analyst",
            password="existing strong password 647!",
        )
        AccountSecurityState.objects.create(user=user)
        current_client = Client(enforce_csrf_checks=True)
        other_client = Client(enforce_csrf_checks=True)
        self.login_client(current_client, "analyst", "existing strong password 647!")
        self.login_client(other_client, "analyst", "existing strong password 647!")

        response = self.post_json(
            current_client,
            "/api/v1/account/sessions/revoke/",
            {"scope": "others"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["revoked"], "others")
        self.assertEqual(current_client.get("/api/v1/watchlist/").status_code, 200)
        self.assertEqual(other_client.get("/api/v1/watchlist/").status_code, 403)

        response = self.post_json(
            current_client,
            "/api/v1/account/sessions/revoke/",
            {"scope": "all"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["authenticated"])
        self.assertEqual(current_client.get("/api/v1/watchlist/").status_code, 403)

    def test_session_epoch_mismatch_fails_closed(self):
        user = get_user_model().objects.create_user(
            username="analyst",
            password="existing strong password 647!",
        )
        AccountSecurityState.objects.create(user=user, session_epoch=2)
        self.login_client(self.client, "analyst", "existing strong password 647!")
        session = self.client.session
        session[SESSION_EPOCH_SESSION_KEY] = 1
        session.save()

        self.assertEqual(self.client.get("/api/v1/watchlist/").status_code, 403)

    def test_epoch_database_failure_is_a_safe_request_id_correlated_503(self):
        user = get_user_model().objects.create_user(
            username="analyst",
            password="existing strong password 647!",
        )
        AccountSecurityState.objects.create(user=user)
        self.client.force_login(user)

        with patch(
            "accounts.middleware.AccountSecurityState.objects.get_or_create",
            side_effect=DatabaseError("private database detail"),
        ):
            response = self.client.get("/api/v1/watchlist/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "database_unavailable")
        self.assertEqual(response.json()["request_id"], response["X-Request-ID"])
        self.assertNotIn("private database detail", response.content.decode())
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_legacy_session_without_epoch_works_until_first_revocation(self):
        user = get_user_model().objects.create_user(
            username="analyst",
            password="existing strong password 647!",
        )
        state = AccountSecurityState.objects.create(user=user, session_epoch=0)
        self.client.force_login(user)

        self.assertEqual(self.client.get("/api/v1/watchlist/").status_code, 200)
        state.session_epoch = 1
        state.save(update_fields=["session_epoch"])
        self.assertEqual(self.client.get("/api/v1/watchlist/").status_code, 403)

    def test_authenticate_login_returns_none_for_unknown_or_inactive_user(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="inactive",
            password="existing strong password 647!",
            is_active=False,
        )
        bad_user = Client(enforce_csrf_checks=True)
        unknown_response = self.login_client(bad_user, "unknown", "existing strong password 647!")
        inactive_response = self.login_client(
            Client(enforce_csrf_checks=True),
            "inactive",
            "existing strong password 647!",
        )
        self.assertEqual(unknown_response.status_code, 403)
        self.assertEqual(inactive_response.status_code, 403)
        self.assert_generic_login_failure(unknown_response)
        self.assert_generic_login_failure(inactive_response)

    def test_username_cooldown_is_persistent_generic_and_expires(self):
        get_user_model().objects.create_user(
            username="analyst",
            password="existing strong password 647!",
        )
        digest = login_identifier_digest("analyst", "127.0.0.1")
        self.assertEqual(digest, login_identifier_digest("ANALYST", "127.0.0.1"))
        self.assertNotEqual(digest, login_identifier_digest("analyst", "127.0.0.2"))

        failures = [
            self.login_client(
                Client(enforce_csrf_checks=True),
                "analyst",
                "incorrect password 991!",
            )
            for _ in range(LOGIN_FAILURE_LIMIT)
        ]
        self.assertTrue(all(response.status_code == 403 for response in failures))
        self.assert_generic_login_failure(failures[0])
        self.assert_generic_login_failure(failures[-1])

        attempt = LoginAttemptState.objects.get(identifier_digest=digest)
        self.assertEqual(attempt.failure_count, LOGIN_FAILURE_LIMIT)
        self.assertIsNotNone(attempt.locked_until)
        original_locked_until = attempt.locked_until
        remaining = original_locked_until - timezone.now()
        self.assertGreater(remaining, LOGIN_COOLDOWN - timedelta(seconds=5))
        self.assertLessEqual(remaining, LOGIN_COOLDOWN)
        self.assertNotIn("analyst", str(attempt))
        self.assertFalse(hasattr(attempt, "username"))

        blocked = self.login_client(
            Client(enforce_csrf_checks=True),
            "analyst",
            "existing strong password 647!",
        )
        self.assertEqual(blocked.status_code, 403)
        attempt.refresh_from_db()
        self.assertEqual(attempt.locked_until, original_locked_until)

        expired_at = timezone.now() - timedelta(seconds=1)
        LoginAttemptState.objects.filter(pk=attempt.pk).update(
            locked_until=expired_at,
            window_started_at=expired_at - LOGIN_ATTEMPT_WINDOW,
            expires_at=expired_at,
        )
        accepted = self.login_client(
            Client(enforce_csrf_checks=True),
            "analyst",
            "existing strong password 647!",
        )
        self.assertEqual(accepted.status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.failure_count, 0)
        self.assertIsNone(attempt.locked_until)
        self.assertLessEqual(attempt.expires_at, timezone.now())

    def test_failed_unknown_username_is_stored_only_as_a_secret_keyed_digest(self):
        username = "unregistered-person"
        digest = login_identifier_digest(username, "127.0.0.1")
        for _ in range(LOGIN_FAILURE_LIMIT):
            response = self.login_client(
                Client(enforce_csrf_checks=True),
                username,
                "incorrect password 991!",
            )
            self.assertEqual(response.status_code, 403)
            self.assert_generic_login_failure(response)

        attempt = LoginAttemptState.objects.get(identifier_digest=digest)
        self.assertEqual(attempt.failure_count, LOGIN_FAILURE_LIMIT)
        self.assertNotIn(username, str(attempt))
        self.assertFalse(hasattr(attempt, "username"))

    def test_login_cooldown_uses_peer_ip_and_ignores_spoofed_forwarded_for(self):
        get_user_model().objects.create_user(
            username="analyst",
            password="existing strong password 647!",
        )
        attacker = Client(enforce_csrf_checks=True)
        for _ in range(LOGIN_FAILURE_LIMIT):
            response = self.login_client(
                attacker,
                "analyst",
                "incorrect password 991!",
                remote_addr="198.51.100.1",
                forwarded_for="198.51.100.2",
            )
            self.assertEqual(response.status_code, 403)

        attacker_retry = self.login_client(
            attacker,
            "analyst",
            "existing strong password 647!",
            remote_addr="198.51.100.1",
        )
        self.assertEqual(attacker_retry.status_code, 403)

        owner = Client(enforce_csrf_checks=True)
        owner_login = self.login_client(
            owner,
            "analyst",
            "existing strong password 647!",
            remote_addr="198.51.100.2",
            forwarded_for="198.51.100.1",
        )
        self.assertEqual(owner_login.status_code, 200)

        attacker_digest = login_identifier_digest("analyst", "198.51.100.1")
        owner_digest = login_identifier_digest("analyst", "198.51.100.2")
        attacker_attempt = LoginAttemptState.objects.get(
            identifier_digest=attacker_digest
        )
        owner_attempt = LoginAttemptState.objects.get(identifier_digest=owner_digest)
        self.assertEqual(attacker_attempt.failure_count, LOGIN_FAILURE_LIMIT)
        self.assertIsNotNone(attacker_attempt.locked_until)
        self.assertEqual(owner_attempt.failure_count, 0)
        self.assertIsNone(owner_attempt.locked_until)

    def test_missing_remote_address_uses_the_unknown_peer_bucket(self):
        request = RequestFactory().post("/api/v1/session/")
        request.META.pop("REMOTE_ADDR", None)

        self.assertIsNone(
            authenticate_login(
                request,
                "unregistered-without-peer",
                "incorrect password 991!",
            )
        )

        attempt = LoginAttemptState.objects.get(
            identifier_digest=login_identifier_digest(
                "unregistered-without-peer",
                "unknown",
            )
        )
        self.assertEqual(attempt.failure_count, 1)

    def test_login_started_before_revocation_cannot_bind_a_new_session(self):
        user = get_user_model().objects.create_user(
            username="analyst",
            password="existing strong password 647!",
        )
        AccountSecurityState.objects.create(user=user)
        request = RequestFactory().post("/api/v1/session/")
        request.session = SessionStore()
        authenticated_user = authenticate_login(
            request,
            "analyst",
            "existing strong password 647!",
        )
        self.assertIsNotNone(authenticated_user)

        _, reset_token = issue_password_reset(user=user, issued_by=self.operator)
        confirm_password_reset(
            token=reset_token,
            password="replacement password after reset 492!",
            confirmation="replacement password after reset 492!",
        )
        with self.assertRaises(LoginInvalidated):
            bind_session(request, authenticated_user)
        self.assertNotIn("_auth_user_id", request.session)
        self.assertTrue(
            get_user_model().objects.get(pk=user.pk).check_password(
                "replacement password after reset 492!"
            )
        )

    def test_token_issue_rejects_lifetimes_over_policy_limit(self):
        with self.assertRaises(ValueError):
            issue_invitation(
                username="analyst",
                issued_by=self.operator,
                expires_in=timedelta(days=8),
            )
        user = get_user_model().objects.create_user(
            username="reset-target",
            password="the old password is strong 892!",
        )
        with self.assertRaises(ValueError):
            issue_password_reset(
                user=user,
                issued_by=self.operator,
                expires_in=timedelta(days=2),
            )


class TokenServiceTests(TestCase):
    def setUp(self):
        self.operator = get_user_model().objects.create_user(
            username="operator",
            password="operator-password-516!secure",
            is_staff=True,
        )

    def test_token_records_store_only_digest(self):
        invitation, token = issue_invitation(username="analyst", issued_by=self.operator)
        self.assertEqual(invitation.token_digest, digest_token(token))
        self.assertNotIn(token, invitation.token_digest)

    def test_invitation_rejects_an_existing_username_without_consuming_token(self):
        invitation, token = issue_invitation(username="analyst", issued_by=self.operator)
        get_user_model().objects.create_user(
            username="analyst",
            password="valid password 739! secure",
        )
        with self.assertRaises(InvalidAccountToken):
            accept_invitation(
                token=token,
                password="an additional valid password 983!",
                confirmation="an additional valid password 983!",
            )
        self.assertIsNone(AccountInvitation.objects.get(pk=invitation.pk).consumed_at)


class AccountManagementCommandTests(TestCase):
    def setUp(self):
        self.operator = get_user_model().objects.create_user(
            username="operator",
            password="operator-password-516!secure",
            is_staff=True,
        )

    def test_invitation_command_prints_private_ui_fragment_once(self):
        output = StringIO()
        call_command(
            "issue_invitation",
            username="invitee",
            issued_by=self.operator.username,
            expires_in_hours=1,
            base_url="https://app.example.com",
            stdout=output,
        )
        rendered = output.getvalue()
        url_line = next(line for line in rendered.splitlines() if line.startswith("Open once: "))
        token = url_line.partition("#token=")[2]
        invitation = AccountInvitation.objects.get()

        self.assertTrue(url_line.startswith("Open once: https://app.example.com/account/accept/"))
        self.assertEqual(len(token), 43)
        self.assertEqual(rendered.count(token), 1)
        self.assertIn(f"Invitation ID: {invitation.pk}", rendered)
        self.assertIn(
            "API endpoint: POST https://app.example.com/api/v1/account/invitations/accept/",
            rendered,
        )
        self.assertEqual(invitation.token_digest, digest_token(token))

    def test_revoke_invitation_blocks_redemption_and_is_idempotent(self):
        invitation, token = issue_invitation(
            username="revoked-invitee",
            issued_by=self.operator,
        )
        call_command(
            "revoke_invitation",
            str(invitation.pk),
            revoked_by=self.operator.username,
            stdout=StringIO(),
        )

        revoked = AccountInvitation.objects.get(pk=invitation.pk)
        self.assertIsNotNone(revoked.revoked_at)
        self.assertTrue(AccountInvitation.objects.filter(pk=invitation.pk).exists())
        revoked_at = revoked.revoked_at
        with self.assertRaises(InvalidAccountToken):
            accept_invitation(
                token=token,
                password="a strong revoked password 794!",
                confirmation="a strong revoked password 794!",
            )

        call_command(
            "revoke_invitation",
            str(invitation.pk),
            revoked_by=self.operator.username,
            stdout=StringIO(),
        )
        revoked.refresh_from_db()
        self.assertEqual(revoked.revoked_at, revoked_at)

    def test_revoke_invitation_requires_active_staff_operator(self):
        invitation, _ = issue_invitation(
            username="staff-only-invitee",
            issued_by=self.operator,
        )
        nonstaff_operator = get_user_model().objects.create_user(
            username="nonstaff-operator",
            password="nonstaff-password-493!",
        )
        inactive_operator = get_user_model().objects.create_user(
            username="inactive-operator",
            password="inactive-password-389!",
            is_staff=True,
            is_active=False,
        )

        for username in (nonstaff_operator.username, inactive_operator.username):
            with self.subTest(username=username):
                with self.assertRaises(CommandError):
                    call_command(
                        "revoke_invitation",
                        str(invitation.pk),
                        revoked_by=username,
                        stdout=StringIO(),
                    )

        invitation.refresh_from_db()
        self.assertIsNone(invitation.revoked_at)

    def test_revoke_invitation_leaves_consumed_token_unchanged(self):
        invitation, token = issue_invitation(
            username="consumed-invitee",
            issued_by=self.operator,
        )
        accept_invitation(
            token=token,
            password="a strong consumed password 637!",
            confirmation="a strong consumed password 637!",
        )
        invitation.refresh_from_db()
        consumed_at = invitation.consumed_at

        call_command(
            "revoke_invitation",
            str(invitation.pk),
            revoked_by=self.operator.username,
            stdout=StringIO(),
        )

        invitation.refresh_from_db()
        self.assertEqual(invitation.consumed_at, consumed_at)
        self.assertIsNone(invitation.revoked_at)
        self.assertTrue(
            get_user_model().objects.filter(username="consumed-invitee").exists()
        )

    def test_reset_command_prints_private_ui_fragment_once(self):
        user = get_user_model().objects.create_user(
            username="reset-target",
            password="the old password is strong 892!",
        )
        output = StringIO()
        call_command(
            "issue_password_reset",
            username=user.username,
            issued_by=self.operator.username,
            expires_in_hours=1,
            base_url="https://app.example.com",
            stdout=output,
        )
        rendered = output.getvalue()
        url_line = next(line for line in rendered.splitlines() if line.startswith("Open once: "))
        token = url_line.partition("#token=")[2]

        self.assertTrue(url_line.startswith("Open once: https://app.example.com/account/reset/"))
        self.assertEqual(len(token), 43)
        self.assertEqual(rendered.count(token), 1)
        self.assertEqual(PasswordResetToken.objects.get().token_digest, digest_token(token))

    def test_issuance_rejects_insecure_origin_and_inactive_issuer_before_writing(self):
        with self.assertRaises(CommandError):
            call_command(
                "issue_invitation",
                username="invitee",
                issued_by=self.operator.username,
                base_url="http://app.example.com",
                stdout=StringIO(),
            )
        self.assertEqual(AccountInvitation.objects.count(), 0)

        inactive_operator = get_user_model().objects.create_user(
            username="inactive-operator",
            password="inactive-password-389!",
            is_staff=True,
            is_active=False,
        )
        with self.assertRaises(CommandError):
            call_command(
                "issue_invitation",
                username="invitee",
                issued_by=inactive_operator.username,
                base_url="https://app.example.com",
                stdout=StringIO(),
            )
        self.assertEqual(AccountInvitation.objects.count(), 0)

    def test_prune_command_removes_only_expired_or_terminal_records(self):
        now = timezone.now()
        active_invitation, _ = issue_invitation(
            username="active-invitee",
            issued_by=self.operator,
        )
        expired_invitation, _ = issue_invitation(
            username="expired-invitee",
            issued_by=self.operator,
        )
        AccountInvitation.objects.filter(pk=expired_invitation.pk).update(
            expires_at=now - timedelta(seconds=1)
        )
        consumed_invitation, _ = issue_invitation(
            username="consumed-invitee",
            issued_by=self.operator,
        )
        AccountInvitation.objects.filter(pk=consumed_invitation.pk).update(
            consumed_at=now
        )

        user = get_user_model().objects.create_user(
            username="reset-target",
            password="the old password is strong 892!",
        )
        AccountSecurityState.objects.create(user=user)
        active_reset, _ = issue_password_reset(user=user, issued_by=self.operator)
        expired_user = get_user_model().objects.create_user(
            username="expired-reset-target",
            password="the old password is strong 892!",
        )
        expired_reset, _ = issue_password_reset(
            user=expired_user,
            issued_by=self.operator,
        )
        PasswordResetToken.objects.filter(pk=expired_reset.pk).update(
            expires_at=now - timedelta(seconds=1)
        )

        LoginAttemptState.objects.create(
            identifier_digest="a" * 64,
            failure_count=1,
            window_started_at=now,
            expires_at=now + timedelta(minutes=15),
        )
        expired_attempt = LoginAttemptState.objects.create(
            identifier_digest="b" * 64,
            failure_count=1,
            window_started_at=now - timedelta(hours=1),
            expires_at=now - timedelta(seconds=1),
        )

        call_command("prune_account_security", stdout=StringIO())

        self.assertTrue(AccountInvitation.objects.filter(pk=active_invitation.pk).exists())
        self.assertFalse(AccountInvitation.objects.filter(pk=expired_invitation.pk).exists())
        self.assertFalse(AccountInvitation.objects.filter(pk=consumed_invitation.pk).exists())
        self.assertTrue(PasswordResetToken.objects.filter(pk=active_reset.pk).exists())
        self.assertFalse(PasswordResetToken.objects.filter(pk=expired_reset.pk).exists())
        self.assertFalse(LoginAttemptState.objects.filter(pk=expired_attempt.pk).exists())
        self.assertEqual(LoginAttemptState.objects.count(), 1)
        self.assertTrue(AccountSecurityState.objects.exists())
