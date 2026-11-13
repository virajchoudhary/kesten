from django.contrib.auth import logout
from django.db import DatabaseError
from django.http import JsonResponse
from operations.logging import current_request_id

from .constants import SESSION_EPOCH_SESSION_KEY
from .models import AccountSecurityState


class SessionEpochMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in {"/health/", "/health/ready/"}:
            return self.get_response(request)
        try:
            user = getattr(request, "user", None)
            if user is not None and user.is_authenticated:
                session_epoch = request.session.get(SESSION_EPOCH_SESSION_KEY, 0)
                state, _ = AccountSecurityState.objects.get_or_create(user_id=user.pk)
                current_epoch = state.session_epoch
                if type(session_epoch) is not int or current_epoch != session_epoch:
                    logout(request)
        except DatabaseError:
            response = JsonResponse(
                {
                    "code": "database_unavailable",
                    "message": "A required service is unavailable. Try again shortly.",
                    "field_errors": {},
                    "request_id": current_request_id(),
                },
                status=503,
            )
            response["Cache-Control"] = "private, no-store"
            response["Referrer-Policy"] = "no-referrer"
            response["Retry-After"] = "1"
            return response

        return self.get_response(request)
