from django.urls import path

from .views import (
    ChangePasswordView,
    InvitationAcceptView,
    PasswordResetConfirmView,
    RevokeSessionsView,
)

urlpatterns = [
    path("invitations/accept/", InvitationAcceptView.as_view(), name="account-invitation-accept"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="account-password-reset-confirm"),
    path("password/change/", ChangePasswordView.as_view(), name="account-password-change"),
    path("sessions/revoke/", RevokeSessionsView.as_view(), name="account-sessions-revoke"),
]
