from ipaddress import ip_address

from django.conf import settings
from django.http import JsonResponse

from .logging import current_request_id


class ClientAddressMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        forwarded = request.headers.get("X-Cadrisyn-Client-IP")
        address = request.META.get("REMOTE_ADDR", "")
        if settings.CADRISYN_TRUST_CLIENT_IP and forwarded:
            try:
                address = str(ip_address(forwarded))
            except ValueError:
                response = JsonResponse({"code": "invalid_client_address", "message": "The request could not be accepted.", "field_errors": {}, "request_id": current_request_id()}, status=400)
                response["Cache-Control"] = "private, no-store"
                return response
        request.META["REMOTE_ADDR"] = address or "unknown"
        return self.get_response(request)
