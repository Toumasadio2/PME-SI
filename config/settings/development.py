"""
Development settings.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# CORS (allow all in dev)
CORS_ALLOW_ALL_ORIGINS = True

# Email (console backend)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable CSRF for easier local testing (HTMX)
# In production, ensure CSRF is properly configured
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
