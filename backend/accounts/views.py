from django.core.exceptions import ValidationError as DjangoValidationError
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from operations.logging import current_request_id
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    AccountErrorSerializer,
    ChangePasswordSerializer,
    InvitationAcceptSerializer,
    InvitationAcceptedSerializer,
    PasswordChangedSerializer,
    PasswordResetConfirmSerializer,
    RevokeSessionsSerializer,
    SessionRevocationSerializer,
)
from .services import (
    IncorrectCurrentPassword,
    InvalidAccountToken,
    accept_invitation,
    change_password,
    confirm_password_reset,
    revoke_sessions,
)


def _error(code, message, status_code, field_errors=None):
    return Response(
        {
            "code": code,
            "message": message,
            "field_errors": field_errors or {},
            "request_id": current_request_id(),
        },
        status=status_code,
    )


class AccountAPIView(APIView):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        response["Referrer-Policy"] = "no-referrer"
        return response


@method_decorator(csrf_protect, name="dispatch")
class InvitationAcceptView(AccountAPIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=InvitationAcceptSerializer,
        responses={
            201: InvitationAcceptedSerializer,
            400: AccountErrorSerializer,
            403: AccountErrorSerializer,
            429: AccountErrorSerializer,
            503: AccountErrorSerializer,
        },
        operation_id="account_invitation_accept",
    )
    def post(self, request):
        serializer = InvitationAcceptSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("invalid_input", "Review the submitted fields.", 400, serializer.errors)
        data = serializer.validated_data
        try:
            accept_invitation(
                token=data["token"],
                password=data["new_password"],
                confirmation=data["confirm_password"],
            )
        except InvalidAccountToken:
            return _error("invalid_invitation", "This invitation is invalid or expired.", 400)
        except DjangoValidationError as error:
            return _error(
                "password_policy",
                "Choose a password that meets the account requirements.",
                400,
                {"new_password": error.messages},
            )
        return Response({"created": True}, status=201)


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetConfirmView(AccountAPIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={
            200: PasswordChangedSerializer,
            400: AccountErrorSerializer,
            403: AccountErrorSerializer,
            429: AccountErrorSerializer,
            503: AccountErrorSerializer,
        },
        operation_id="account_password_reset_confirm",
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("invalid_input", "Review the submitted fields.", 400, serializer.errors)
        data = serializer.validated_data
        try:
            confirm_password_reset(
                token=data["token"],
                password=data["new_password"],
                confirmation=data["confirm_password"],
            )
        except InvalidAccountToken:
            return _error("invalid_reset_token", "This reset token is invalid or expired.", 400)
        except DjangoValidationError as error:
            return _error(
                "password_policy",
                "Choose a password that meets the account requirements.",
                400,
                {"new_password": error.messages},
            )
        return Response({"password_changed": True}, status=200)


@method_decorator(csrf_protect, name="dispatch")
class ChangePasswordView(AccountAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: PasswordChangedSerializer,
            400: AccountErrorSerializer,
            403: AccountErrorSerializer,
            503: AccountErrorSerializer,
        },
        operation_id="account_password_change",
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("invalid_input", "Review the submitted fields.", 400, serializer.errors)
        data = serializer.validated_data
        try:
            change_password(
                request=request,
                user=request.user,
                current_password=data["current_password"],
                password=data["new_password"],
                confirmation=data["confirm_password"],
            )
        except IncorrectCurrentPassword:
            return _error(
                "invalid_current_password",
                "The current password is incorrect.",
                400,
                {"current_password": ["The current password is incorrect."]},
            )
        except DjangoValidationError as error:
            return _error(
                "password_policy",
                "Choose a password that meets the account requirements.",
                400,
                {"new_password": error.messages},
            )
        return Response({"password_changed": True}, status=200)


@method_decorator(csrf_protect, name="dispatch")
class RevokeSessionsView(AccountAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=RevokeSessionsSerializer,
        responses={
            200: SessionRevocationSerializer,
            400: AccountErrorSerializer,
            403: AccountErrorSerializer,
            503: AccountErrorSerializer,
        },
        operation_id="account_sessions_revoke",
    )
    def post(self, request):
        serializer = RevokeSessionsSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("invalid_input", "Choose a supported revocation scope.", 400, serializer.errors)

        scope = serializer.validated_data["scope"]
        revoke_sessions(request=request, user=request.user, scope=scope)
        return Response(
            {
                "revoked": scope,
                "authenticated": scope != "all",
                "csrf_token": get_token(request) if scope != "all" else None,
            },
            status=200,
        )
