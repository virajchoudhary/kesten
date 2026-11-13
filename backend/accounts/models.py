from django.conf import settings
from django.db import models
from django.utils import timezone


class AccountSecurityState(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_security_state",
    )
    session_epoch = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Account security state for user {self.user_id}"


class AccountInvitation(models.Model):
    reserved_username = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    token_digest = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="account_invitations_issued",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["reserved_username", "consumed_at", "revoked_at"],
                name="acct_invite_status",
            )
        ]

    def __str__(self):
        return f"Invitation for {self.reserved_username}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_password_reset_tokens",
    )
    token_digest = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="account_password_resets_issued",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "expires_at"], name="acct_reset_user_expiry")
        ]

    def __str__(self):
        return f"Password reset token for user {self.user_id}"


class LoginAttemptState(models.Model):
    identifier_digest = models.CharField(max_length=64, unique=True, editable=False)
    failure_count = models.PositiveSmallIntegerField(default=0)
    window_started_at = models.DateTimeField(default=timezone.now)
    locked_until = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Hashed login attempt state"
