"""WSGI config for SpecShift API."""

import os
import secrets
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.config.settings")
if os.getenv("RENDER") and not os.getenv("DJANGO_SECRET_KEY"):
    # No sessions or signed persisted values exist in this stateless release.
    # An instance-local secret avoids exposing a generated credential in tooling.
    os.environ["DJANGO_SECRET_KEY"] = secrets.token_urlsafe(64)

application = get_wsgi_application()
