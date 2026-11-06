import math
import re
import uuid
from datetime import date

from django.conf import settings
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.decorators import api_view
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

class LegacyBasicAuthentication(BasicAuthentication):
    def authenticate(self, request):
        authorization = get_authorization_header(request).split()
        if authorization and authorization[0].lower() == b"basic" and request.headers.get("X-Cadrisyn-Research") != "1":
            raise AuthenticationFailed("Use the configured local research client.")
        return super().authenticate(request)


LEGACY_AUTHENTICATION_CLASSES = [LegacyBasicAuthentication, SessionAuthentication]
_SESSION_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,64}\Z", re.ASCII)
_TICKER_RE = re.compile(r"[A-Za-z0-9.^=_-]{1,20}\Z", re.ASCII)
_ISO_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", re.ASCII)


class LegacyOperatorPermission(BasePermission):
    message = "Legacy research endpoints are unavailable."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            settings.CADRISYN_LEGACY_ENABLED
            and user
            and user.is_authenticated
            and user.is_staff
        )


class LegacyOperatorAPIView(APIView):
    authentication_classes = LEGACY_AUTHENTICATION_CLASSES
    permission_classes = [LegacyOperatorPermission]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "legacy"


def legacy_api_view(methods, throttle_scope="legacy"):
    def decorate(view_function):
        view = api_view(methods)(view_function)
        view.cls.authentication_classes = LEGACY_AUTHENTICATION_CLASSES
        view.cls.permission_classes = [LegacyOperatorPermission]
        view.cls.throttle_classes = [ScopedRateThrottle]
        view.cls.throttle_scope = throttle_scope
        return view

    return decorate


def legacy_error_response(request, code, message, http_status, field_errors=None):
    request_id = getattr(request, "request_id", None) or uuid.uuid4().hex
    return Response(
        {
            "code": code,
            "message": message,
            "field_errors": field_errors or {},
            "request_id": request_id,
        },
        status=http_status,
    )


def normalize_ticker(value):
    if not isinstance(value, str):
        raise ValueError("Invalid ticker.")
    symbol = value.strip().upper()
    if not _TICKER_RE.fullmatch(symbol):
        raise ValueError("Invalid ticker.")
    return symbol


def normalize_tickers(value, minimum=1, maximum=20):
    if not isinstance(value, (list, tuple)) or not minimum <= len(value) <= maximum:
        raise ValueError("Invalid ticker list.")
    symbols = [normalize_ticker(item) for item in value]
    if len(set(symbols)) != len(symbols):
        raise ValueError("Ticker list must not contain duplicates.")
    return symbols


def is_safe_legacy_session_id(value):
    return isinstance(value, str) and bool(_SESSION_ID_RE.fullmatch(value))


def bounded_int(value, minimum, maximum, default=None):
    if value is None and default is not None:
        value = default
    if isinstance(value, bool):
        raise ValueError("Invalid integer.")
    if isinstance(value, int):
        result = value
    elif isinstance(value, str) and value.isascii() and value.isdecimal():
        result = int(value)
    else:
        raise ValueError("Invalid integer.")
    if not minimum <= result <= maximum:
        raise ValueError("Integer is outside the supported range.")
    return result


def bounded_float(value, minimum, maximum, default=None):
    if value is None and default is not None:
        value = default
    if isinstance(value, bool):
        raise ValueError("Invalid number.")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Invalid number.") from error
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValueError("Number is outside the supported range.")
    return result


def parse_bool(value, default=None):
    if value is None:
        if default is None:
            raise ValueError("Invalid boolean.")
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise ValueError("Invalid boolean.")


def optional_iso_date(value):
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not _ISO_DATE_RE.fullmatch(value):
        raise ValueError("Invalid date.")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError("Invalid date.") from error
