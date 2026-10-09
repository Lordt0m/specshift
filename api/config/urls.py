"""URL configuration for SpecShift API."""

from django.urls import path
from api.views import HealthView, PolicyView, CompareView, ReportView

urlpatterns = [
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/policy/v1/", PolicyView.as_view(), name="policy"),
    path("api/compare/", CompareView.as_view(), name="compare"),
    path("api/report/", ReportView.as_view(), name="report"),
]
