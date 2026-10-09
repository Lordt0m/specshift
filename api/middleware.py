"""Bounded stateless ingress; no uploaded content is saved or logged."""
import io
import os
import threading
import time
from collections import OrderedDict
from django.http import JsonResponse

MAX_WIRE_BYTES = 4 * 1024 * 1024
_slots = threading.BoundedSemaphore(1)
_lock = threading.Lock()
_buckets = OrderedDict()


class PublicRequestBoundary:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path not in {"/api/compare/", "/api/report/"} or request.method != "POST":
            return self.get_response(request)
        if os.getenv("PUBLIC_COMPARE_ENABLED", "true").lower() != "true":
            return JsonResponse({"code": "COMPARE_DISABLED", "message": "Live comparison is temporarily unavailable."}, status=503)
        # Use REMOTE_ADDR rather than trusting client-supplied forwarded IPs.
        # A shared proxy can conservatively throttle multiple visitors together.
        key = request.META.get("REMOTE_ADDR", "unknown")
        now = time.monotonic()
        with _lock:
            start, count = _buckets.pop(key, (now, 0))
            if now - start >= 60:
                start, count = now, 0
            _buckets[key] = (start, count + 1)
            while len(_buckets) > 1024:
                _buckets.popitem(last=False)
        if count >= 10:
            response = JsonResponse({"code": "RATE_LIMIT", "message": "Too many comparisons. Retry in a minute."}, status=429)
            response["Retry-After"] = "60"
            return response
        if not _slots.acquire(blocking=False):
            return JsonResponse({"code": "BUSY", "message": "Another comparison is running. Retry shortly."}, status=503)
        try:
            raw = request._stream.read(MAX_WIRE_BYTES + 1)
            if len(raw) > MAX_WIRE_BYTES:
                return JsonResponse({"code": "BODY_TOO_LARGE", "message": "Request exceeds the 4 MiB wire limit."}, status=413)
            request._body = raw
            request._stream = io.BytesIO(raw)
            response = self.get_response(request)
            response["Cache-Control"] = "no-store"
            return response
        finally:
            _slots.release()
