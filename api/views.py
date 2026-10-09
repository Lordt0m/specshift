"""Django REST Framework views for SpecShift.

Exposes health, policy metadata, comparison, and HTML report endpoints.
Enforces limits and privacy controls per architecture.md and security-and-privacy.md.
"""

from typing import Any, Tuple
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .comparison.engine import compare_specifications, SCHEMA_VERSION, ENGINE_VERSION, ComparisonTimeoutError
from .comparison.parse import (
    ParseError,
    DocumentSizeLimitError,
    NestingDepthLimitError,
    DuplicateKeyError,
    UnsupportedOpenAPIVersionError,
    ExternalReferenceError,
    MissingInternalReferenceError,
    SUPPORTED_VERSIONS,
    MAX_DOCUMENT_BYTES,
)
from .comparison.rules import RULE_REGISTRY, POLICY_VERSION
from .comparison.report import generate_html_report


class HealthView(APIView):
    """GET /api/health/ - readiness and version check without user data."""
    def get(self, request: Request) -> JsonResponse:
        return JsonResponse({
            "status": "ok",
            "schema_version": SCHEMA_VERSION,
            "engine_version": ENGINE_VERSION,
            "policy_version": POLICY_VERSION,
            "supported_openapi_versions": sorted(list(SUPPORTED_VERSIONS)),
        })


class PolicyView(APIView):
    """GET /api/policy/v1/ - machine-readable rules, constraints, and limits."""
    def get(self, request: Request) -> JsonResponse:
        rules_data = [
            {
                "id": r.id,
                "title": r.title,
                "request_classification": r.request_classification,
                "response_classification": r.response_classification,
                "description": r.description,
                "assumptions": r.assumptions,
            }
            for r in sorted(RULE_REGISTRY.values(), key=lambda x: x.id)
        ]
        return JsonResponse({
            "policy_version": POLICY_VERSION,
            "engine_version": ENGINE_VERSION,
            "supported_openapi_versions": sorted(list(SUPPORTED_VERSIONS)),
            "max_document_size_bytes": MAX_DOCUMENT_BYTES,
            "rules": rules_data,
        })


def _extract_inputs(request: Request) -> Tuple[bytes, bytes]:
    """Extract baseline and candidate bytes from JSON body or uploaded files."""
    baseline_bytes: bytes = b""
    candidate_bytes: bytes = b""

    # Try files first
    if "baseline" in request.FILES:
        baseline_bytes = request.FILES["baseline"].read(MAX_DOCUMENT_BYTES + 1)
    elif isinstance(request.data, dict) and "baseline" in request.data:
        val = request.data["baseline"]
        if not isinstance(val, str):
            raise ValueError("Baseline must be a document string.")
        baseline_bytes = val.encode("utf-8")

    if "candidate" in request.FILES:
        candidate_bytes = request.FILES["candidate"].read(MAX_DOCUMENT_BYTES + 1)
    elif isinstance(request.data, dict) and "candidate" in request.data:
        val = request.data["candidate"]
        if not isinstance(val, str):
            raise ValueError("Candidate must be a document string.")
        candidate_bytes = val.encode("utf-8")

    if not baseline_bytes:
        raise ValueError("Baseline specification is required (as file upload or string property).")
    if not candidate_bytes:
        raise ValueError("Candidate specification is required (as file upload or string property).")

    return baseline_bytes, candidate_bytes


from django.core.exceptions import RequestDataTooBig


def _handle_comparison_error(exc: Exception) -> Tuple[dict[str, Any], int]:
    """Map comparison exceptions to stable error codes and HTTP statuses."""
    if isinstance(exc, ComparisonTimeoutError):
        return {"code": "WORK_DEADLINE", "message": str(exc)}, 503
    if isinstance(exc, (DocumentSizeLimitError, RequestDataTooBig)):
        return {
            "code": "DOCUMENT_SIZE_EXCEEDED",
            "message": str(exc),
        }, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    elif isinstance(exc, NestingDepthLimitError):
        return {
            "code": "NESTING_DEPTH_EXCEEDED",
            "message": str(exc),
        }, status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, DuplicateKeyError):
        return {
            "code": "DUPLICATE_KEY",
            "message": str(exc),
        }, status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, UnsupportedOpenAPIVersionError):
        return {
            "code": "UNSUPPORTED_OPENAPI_VERSION",
            "message": str(exc),
        }, status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, ExternalReferenceError):
        return {
            "code": "EXTERNAL_REFERENCE_PROHIBITED",
            "message": str(exc),
        }, status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, MissingInternalReferenceError):
        return {
            "code": "MISSING_INTERNAL_REFERENCE",
            "message": str(exc),
        }, status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, ParseError):
        return {
            "code": "MALFORMED_SPECIFICATION",
            "message": str(exc),
        }, status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, ValueError):
        return {
            "code": "MISSING_INPUT",
            "message": str(exc),
        }, status.HTTP_400_BAD_REQUEST
    else:
        return {
            "code": "COMPARISON_FAILED",
            "message": "An unexpected error occurred during comparison.",
        }, status.HTTP_500_INTERNAL_SERVER_ERROR


class CompareView(APIView):
    """POST /api/compare/ - compare two OpenAPI specifications in-memory."""
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request: Request) -> JsonResponse:
        try:
            baseline_bytes, candidate_bytes = _extract_inputs(request)
            result = compare_specifications(baseline_bytes, candidate_bytes)
            return JsonResponse(result, status=status.HTTP_200_OK)
        except Exception as exc:
            err_data, status_code = _handle_comparison_error(exc)
            return JsonResponse(err_data, status=status_code)


class ReportView(APIView):
    """POST /api/report/ - generate server-side escaped HTML report download."""
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request: Request) -> HttpResponse:
        try:
            baseline_bytes, candidate_bytes = _extract_inputs(request)
            result = compare_specifications(baseline_bytes, candidate_bytes)
            html_content = generate_html_report(result)
            response = HttpResponse(html_content, content_type="text/html; charset=utf-8")
            response["Content-Disposition"] = 'attachment; filename="specshift-report.html"'
            return response
        except Exception as exc:
            err_data, status_code = _handle_comparison_error(exc)
            return JsonResponse(err_data, status=status_code)
