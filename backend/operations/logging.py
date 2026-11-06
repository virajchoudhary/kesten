"""Request diagnostics deliberately exclude bodies, query strings and credentials."""

import json
import logging
import re
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from django.conf import settings

request_id = ContextVar("request_id", default=None)
logger = logging.getLogger("cadrisyn.requests")


def current_request_id():
    return request_id.get() or uuid.uuid4().hex


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", record.name),
            "request_id": request_id.get(),
        }
        for field in ("method", "route", "status", "duration_ms", "component"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info and record.exc_info[0]:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, separators=(",", ":"))


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        forwarded_id = request.headers.get("X-Request-ID", "")
        trusted_id = settings.CADRISYN_TRUST_REQUEST_ID and re.fullmatch(r"[a-f0-9]{32}", forwarded_id)
        token = request_id.set(forwarded_id if trusted_id else uuid.uuid4().hex)
        request.request_id = request_id.get()
        started = time.monotonic()
        response = None
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id.get()
            if request.path.startswith("/api/"):
                response["Cache-Control"] = "private, no-store"
            return response
        finally:
            match = getattr(request, "resolver_match", None)
            logger.info("request", extra={
                "event": "http_request",
                "method": request.method,
                "route": match.route if match else "unmatched",
                "status": response.status_code if response is not None else 500,
                "duration_ms": round((time.monotonic() - started) * 1000, 2),
            })
            request_id.reset(token)
