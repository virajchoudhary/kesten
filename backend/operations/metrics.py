import os
import threading
import time
from collections import Counter

from django.http import JsonResponse
from django.views.decorators.http import require_GET

_started = time.monotonic()
_lock = threading.Lock()
_statuses = Counter()
_requests = 0
_seconds = 0.0


def record_request(status, duration_seconds):
    global _requests, _seconds
    with _lock:
        _requests += 1
        _seconds += duration_seconds
        _statuses[f'{status // 100}xx'] += 1


@require_GET
def metrics(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        response = JsonResponse({'code': 'permission_denied', 'message': 'Operator access is required.'}, status=403)
    else:
        with _lock:
            payload = {
                'scope': 'single_worker',
                'process_id': os.getpid(),
                'uptime_seconds': round(time.monotonic() - _started, 3),
                'requests_total': _requests,
                'request_duration_seconds_total': round(_seconds, 6),
                'status_classes': dict(_statuses),
            }
        response = JsonResponse(payload)
    response['Cache-Control'] = 'private, no-store'
    return response
