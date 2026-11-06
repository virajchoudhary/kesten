import hashlib
import hmac
import secrets
from datetime import timedelta
from ipaddress import ip_address

from django.conf import settings
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import APIException

from .constants import LOGIN_EPOCH_REQUEST_ATTR, SESSION_EPOCH_SESSION_KEY
from .models import (
    AccountInvitation,
    AccountSecurityState,
    LoginAttemptState,
    PasswordResetToken,
)

MAX_INVITATION_LIFETIME = timedelta(days=7)
MAX_PASSWORD_RESET_LIFETIME = timedelta(hours=24)
LOGIN_FAILURE_LIMIT = 5
LOGIN_ATTEMPT_WINDOW = timedelta(minutes=15)
LOGIN_COOLDOWN = timedelta(minutes=15)


class InvalidAccountToken(Exception):
    pass


class IncorrectCurrentPassword(Exception):
    pass


class LoginInvalidated(APIException):
    """A credential check became stale before its session could be bound."""

    status_code = 403
    default_detail = "The username or password is incorrect."
    default_code = "invalid_credentials"


def digest_token(token):
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def _presented_token_digest(token):
    try:
        return digest_token(token)
    except (AttributeError, UnicodeEncodeError):
        raise InvalidAccountToken from None


def login_identifier_digest(username, client_ip):
    normalized_username = get_user_model().normalize_username(username)
    identifier = normalized_username.casefold()
    peer_address = (
        "unknown" if client_ip == "unknown" else str(ip_address(client_ip))
    )
    payload = f"{identifier}\0{peer_address}".encode("utf-8")
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def _lock_login_attempt(identifier_digest, now):
    try:
        return LoginAttemptState.objects.select_for_update().get(
            identifier_digest=identifier_digest
        )
    except LoginAttemptState.DoesNotExist:
        try:
            with transaction.atomic():
                return LoginAttemptState.objects.create(
                    identifier_digest=identifier_digest,
                    expires_at=now + LOGIN_ATTEMPT_WINDOW,
                )
        except IntegrityError:
            return LoginAttemptState.objects.select_for_update().get(
                identifier_digest=identifier_digest
            )


def authenticate_login(request, username, password):
    client_ip = request.META.get("REMOTE_ADDR", "unknown")
    identifier_digest = login_identifier_digest(username, client_ip)
    attempted_at = timezone.now()

    with transaction.atomic():
        attempt = _lock_login_attempt(identifier_digest, attempted_at)
        now = timezone.now()
        if attempt.locked_until is not None and attempt.locked_until > now:
            return None

        if (
            attempt.locked_until is not None
            or attempt.window_started_at + LOGIN_ATTEMPT_WINDOW <= now
        ):
            attempt.failure_count = 0
            attempt.window_started_at = now
            attempt.locked_until = None

        user = authenticate(request, username=username, password=password)
        if user is None:
            attempt.failure_count = min(attempt.failure_count + 1, LOGIN_FAILURE_LIMIT)
            if attempt.failure_count >= LOGIN_FAILURE_LIMIT:
                attempt.locked_until = now + LOGIN_COOLDOWN
            attempt.expires_at = (
                attempt.locked_until or attempt.window_started_at + LOGIN_ATTEMPT_WINDOW
            )
            attempt.save(
                update_fields=[
                    "failure_count",
                    "window_started_at",
                    "locked_until",
                    "expires_at",
                    "updated_at",
                ]
            )
            return None

        locked_user = get_user_model()._default_manager.select_for_update().get(pk=user.pk)
        if (
            not locked_user.is_active
            or not hmac.compare_digest(locked_user.password, user.password)
        ):
            user = None
        else:
            state = _lock_security_state(locked_user)
            setattr(request, LOGIN_EPOCH_REQUEST_ATTR, state.session_epoch)

        attempt.failure_count = 0
        attempt.window_started_at = now
        attempt.locked_until = None
        attempt.expires_at = now
        attempt.save(
            update_fields=[
                "failure_count",
                "window_started_at",
                "locked_until",
                "expires_at",
                "updated_at",
            ]
        )
        return user


def bind_session(request, user):
    if not user.is_active:
        raise LoginInvalidated

    with transaction.atomic():
        locked_user = get_user_model()._default_manager.select_for_update().get(pk=user.pk)
        if not locked_user.is_active or not hmac.compare_digest(
            locked_user.password,
            user.password,
        ):
            raise LoginInvalidated
        state = _lock_security_state(locked_user)
        expected_epoch = getattr(request, LOGIN_EPOCH_REQUEST_ATTR, None)
        if expected_epoch is None or expected_epoch != state.session_epoch:
            raise LoginInvalidated
        backend = getattr(user, "backend", None)
        if backend:
            locked_user.backend = backend
        login(request, locked_user)
        request.session[SESSION_EPOCH_SESSION_KEY] = state.session_epoch
        return state.session_epoch


def _validate_lifetime(expires_in, maximum):
    if not isinstance(expires_in, timedelta) or expires_in <= timedelta(0) or expires_in > maximum:
        raise ValueError("Token expiry is outside the supported lifetime.")


def _new_token():
    token = secrets.token_urlsafe(32)
    return token, digest_token(token)


def _validate_issuer(issued_by):
    if not issued_by.is_active or not issued_by.is_staff:
        raise ValueError("Token issuance requires an active staff account.")


def issue_invitation(*, username, issued_by, expires_in=timedelta(days=1), email=""):
    _validate_lifetime(expires_in, MAX_INVITATION_LIFETIME)
    _validate_issuer(issued_by)
    user_model = get_user_model()
    normalized_username = user_model.normalize_username(username)
    if not normalized_username:
        raise ValueError("An invitation must reserve a username.")
    username_field = user_model._meta.get_field(user_model.USERNAME_FIELD)
    username_field.clean(normalized_username, None)
    email = user_model._meta.get_field("email").clean(email, None)
    if user_model._default_manager.filter(username=normalized_username).exists():
        raise ValueError("An account with this username already exists.")

    token, token_digest = _new_token()
    invitation = AccountInvitation.objects.create(
        reserved_username=normalized_username,
        email=email,
        token_digest=token_digest,
        expires_at=timezone.now() + expires_in,
        issued_by=issued_by,
    )
    return invitation, token


def revoke_invitation(*, invitation_id, revoked_by):
    user_model = get_user_model()
    with transaction.atomic():
        try:
            operator = user_model._default_manager.select_for_update().get(
                pk=revoked_by.pk
            )
        except user_model.DoesNotExist:
            raise ValueError(
                "Invitation revocation requires an active staff account."
            ) from None
        if not operator.is_active or not operator.is_staff:
            raise ValueError(
                "Invitation revocation requires an active staff account."
            )

        invitation = AccountInvitation.objects.select_for_update().get(
            pk=invitation_id
        )
        if invitation.consumed_at is None and invitation.revoked_at is None:
            invitation.revoked_at = timezone.now()
            invitation.save(update_fields=["revoked_at"])
    return invitation


def issue_password_reset(*, user, issued_by, expires_in=timedelta(hours=1)):
    _validate_lifetime(expires_in, MAX_PASSWORD_RESET_LIFETIME)
    _validate_issuer(issued_by)
    if not user.is_active:
        raise ValueError("Password reset tokens cannot be issued for inactive accounts.")

    token, token_digest = _new_token()
    with transaction.atomic():
        user_model = get_user_model()
        locked_user = user_model._default_manager.select_for_update().get(pk=user.pk)
        if not locked_user.is_active:
            raise ValueError("Password reset tokens cannot be issued for inactive accounts.")

        now = timezone.now()
        PasswordResetToken.objects.filter(
            user=locked_user,
            consumed_at__isnull=True,
            revoked_at__isnull=True,
        ).update(revoked_at=now)
        reset = PasswordResetToken.objects.create(
            user=locked_user,
            token_digest=token_digest,
            expires_at=now + expires_in,
            issued_by=issued_by,
        )
    return reset, token


def _lock_security_state(user):
    AccountSecurityState.objects.get_or_create(user=user)
    return AccountSecurityState.objects.select_for_update().get(user=user)


def _validate_new_password(user, password, confirmation):
    if password != confirmation:
        raise ValidationError({"confirm_password": ["The passwords do not match."]})
    validate_password(password, user=user)


def accept_invitation(*, token, password, confirmation):
    token_digest = _presented_token_digest(token)
    user_model = get_user_model()

    try:
        with transaction.atomic():
            invitation = (
                AccountInvitation.objects.select_for_update()
                .filter(token_digest=token_digest)
                .first()
            )
            now = timezone.now()
            if (
                invitation is None
                or invitation.consumed_at is not None
                or invitation.revoked_at is not None
                or invitation.expires_at <= now
            ):
                raise InvalidAccountToken

            user = user_model(
                username=invitation.reserved_username,
                email=invitation.email,
                is_active=True,
            )
            _validate_new_password(user, password, confirmation)
            user.set_password(password)
            user.save(force_insert=True)
            AccountSecurityState.objects.create(user=user)
            invitation.consumed_at = now
            invitation.save(update_fields=["consumed_at"])
    except IntegrityError as error:
        raise InvalidAccountToken from error

    return user


def confirm_password_reset(*, token, password, confirmation):
    token_digest = _presented_token_digest(token)
    user_model = get_user_model()

    with transaction.atomic():
        candidate_user_id = (
            PasswordResetToken.objects.filter(token_digest=token_digest)
            .values_list("user_id", flat=True)
            .first()
        )
        if candidate_user_id is None:
            raise InvalidAccountToken
        try:
            user = user_model._default_manager.select_for_update().get(
                pk=candidate_user_id
            )
        except user_model.DoesNotExist:
            raise InvalidAccountToken from None
        reset = (
            PasswordResetToken.objects.select_for_update()
            .filter(token_digest=token_digest, user_id=user.pk)
            .first()
        )
        now = timezone.now()
        if (
            reset is None
            or reset.consumed_at is not None
            or reset.revoked_at is not None
            or reset.expires_at <= now
        ):
            raise InvalidAccountToken

        if not user.is_active:
            raise InvalidAccountToken
        _validate_new_password(user, password, confirmation)
        state = _lock_security_state(user)

        user.set_password(password)
        user.save(update_fields=["password"])
        state.session_epoch += 1
        state.save(update_fields=["session_epoch", "updated_at"])
        reset.consumed_at = now
        reset.save(update_fields=["consumed_at"])

    return user


def change_password(*, request, user, current_password, password, confirmation):
    user_model = get_user_model()
    with transaction.atomic():
        locked_user = user_model._default_manager.select_for_update().get(pk=user.pk)
        if not locked_user.check_password(current_password):
            raise IncorrectCurrentPassword
        _validate_new_password(locked_user, password, confirmation)

        state = _lock_security_state(locked_user)
        locked_user.set_password(password)
        locked_user.save(update_fields=["password"])
        state.session_epoch += 1
        state.save(update_fields=["session_epoch", "updated_at"])
        epoch = state.session_epoch

    update_session_auth_hash(request, locked_user)
    request.session[SESSION_EPOCH_SESSION_KEY] = epoch
    return epoch


def revoke_sessions(*, request, user, scope):
    if scope not in {"others", "all"}:
        raise ValueError("Session revocation scope must be 'others' or 'all'.")

    user_model = get_user_model()
    with transaction.atomic():
        locked_user = user_model._default_manager.select_for_update().get(pk=user.pk)
        state = _lock_security_state(locked_user)
        state.session_epoch += 1
        state.save(update_fields=["session_epoch", "updated_at"])
        epoch = state.session_epoch

    if scope == "all":
        logout(request)
    else:
        request.session.cycle_key()
        request.session[SESSION_EPOCH_SESSION_KEY] = epoch
    return epoch
