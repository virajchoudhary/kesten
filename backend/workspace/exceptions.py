import logging

from django.core.exceptions import RequestDataTooBig
from django.db import DatabaseError
from django.http import JsonResponse
from redis.exceptions import RedisError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from operations.logging import current_request_id

logger = logging.getLogger(__name__)


def exception_handler(error, context):
    if isinstance(error, (RedisError, DatabaseError)):
        code = "cache_unavailable" if isinstance(error, RedisError) else "database_unavailable"
        return Response({"code": code, "message": "A required service is unavailable. Try again shortly.", "field_errors": {}, "request_id": current_request_id()}, status=503)
    if isinstance(error, RequestDataTooBig):
        return Response({"code": "request_too_large", "message": "The request body exceeds the allowed size.", "field_errors": {}, "request_id": current_request_id()}, status=413)
    response = drf_exception_handler(error, context)
    if response is None:
        request_id = current_request_id()
        logger.error("API request failed request_id=%s", request_id, exc_info=error)
        return Response({"code": "internal_error", "message": "The request could not be completed.", "field_errors": {}, "request_id": request_id}, status=500)
    detail = response.data
    message = str(detail.get("detail", "The request could not be completed.")) if isinstance(detail, dict) else "The request could not be completed."
    code = {400: "invalid_input", 401: "authentication_required", 403: "permission_denied", 404: "not_found", 429: "rate_limited"}.get(response.status_code, "request_failed")
    response.data = {"code": code, "message": message, "field_errors": detail if response.status_code == 400 else {}, "request_id": current_request_id()}
    return response


def csrf_failure(request, reason=""):
    return JsonResponse({"code": "csrf_failed", "message": "Refresh your session and try again.", "field_errors": {}, "request_id": current_request_id()}, status=403)
