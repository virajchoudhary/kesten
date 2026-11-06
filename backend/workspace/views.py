import uuid

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .instruments import BY_ID, find_instruments
from .market_data import MarketDataUnavailable, get_market_response
from .models import WatchlistEntry
from .serializers import (
    BarQuerySerializer,
    ErrorSerializer,
    InstrumentListSerializer,
    LoginSerializer,
    MarketResponseSerializer,
    SearchSerializer,
    SessionSerializer,
    WatchlistInputSerializer,
)


def session_payload(request):
    user = request.user
    return {
        "authenticated": user.is_authenticated,
        "user": {"username": user.get_username(), "is_staff": user.is_staff} if user.is_authenticated else None,
        "csrf_token": get_token(request),
        "market_data_enabled": getattr(settings, "CADRISYN_MARKET_DATA_ENABLED", False),
        "legacy_enabled": getattr(settings, "CADRISYN_LEGACY_ENABLED", False),
    }


def api_error(code, message, http_status, fields=None):
    return Response({"code": code, "message": message, "field_errors": fields or {}, "request_id": uuid.uuid4().hex}, status=http_status)


class PrivateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


@method_decorator(csrf_protect, name="dispatch")
class SessionView(PrivateAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(responses=SessionSerializer, operation_id="session_read")
    def get(self, request):
        return Response(session_payload(request))

    @extend_schema(request=LoginSerializer, responses={200: SessionSerializer, 400: ErrorSerializer, 403: ErrorSerializer}, operation_id="session_login")
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error("invalid_input", "Enter a username and password.", 400, serializer.errors)
        user = authenticate(request, **serializer.validated_data)
        if user is None:
            return api_error("invalid_credentials", "The username or password is incorrect.", 403)
        login(request, user)
        return Response(session_payload(request))

    @extend_schema(responses=SessionSerializer, operation_id="session_logout")
    def delete(self, request):
        logout(request)
        return Response(session_payload(request))


class InstrumentsView(PrivateAPIView):
    @extend_schema(parameters=[SearchSerializer], responses=InstrumentListSerializer, operation_id="instruments_search")
    def get(self, request):
        serializer = SearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return api_error("invalid_query", "Search is limited to 80 characters.", 400, serializer.errors)
        return Response({"items": find_instruments(serializer.validated_data["query"])})


class BarsView(PrivateAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "market"

    @extend_schema(parameters=[BarQuerySerializer], responses={200: MarketResponseSerializer, 400: ErrorSerializer, 404: ErrorSerializer, 503: ErrorSerializer}, operation_id="instrument_bars")
    def get(self, request, instrument_id):
        instrument = BY_ID.get(instrument_id)
        if instrument is None:
            return api_error("instrument_not_found", "This instrument is outside the supported universe.", 404)
        serializer = BarQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return api_error("invalid_query", "Choose a supported range and data mode.", 400, serializer.errors)
        try:
            result = get_market_response(instrument, serializer.validated_data["range"], serializer.validated_data["mode"])
        except MarketDataUnavailable as error:
            return api_error("market_data_unavailable", str(error), 503)
        return Response(result)


class WatchlistView(PrivateAPIView):
    @extend_schema(responses=InstrumentListSerializer, operation_id="watchlist_read")
    def get(self, request):
        ids = WatchlistEntry.objects.filter(owner=request.user).values_list("instrument_id", flat=True)
        return Response({"items": [BY_ID[item].to_dict() for item in ids if item in BY_ID]})

    @extend_schema(request=WatchlistInputSerializer, responses={201: InstrumentListSerializer, 200: InstrumentListSerializer, 400: ErrorSerializer}, operation_id="watchlist_add")
    def post(self, request):
        serializer = WatchlistInputSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error("invalid_instrument", "Choose a supported instrument.", 400, serializer.errors)
        _, created = WatchlistEntry.objects.get_or_create(owner=request.user, **serializer.validated_data)
        response = self.get(request)
        response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return response


class WatchlistItemView(PrivateAPIView):
    @extend_schema(responses={204: None}, operation_id="watchlist_remove")
    def delete(self, request, instrument_id):
        WatchlistEntry.objects.filter(owner=request.user, instrument_id=instrument_id).delete()
        return Response(status=204)


def health(request):
    return JsonResponse({"status": "ok", "service": "cadrisyn-api"})
