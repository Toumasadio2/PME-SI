"""
Development settings.
"""
from pathlib import Path
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Remove postgres contrib app for SQLite compatibility
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django.contrib.postgres"]  # noqa: F405

# Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# Database - SQLite for local development without PostgreSQL
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Cache - Local memory cache (no Redis needed)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Session - Use database instead of cache
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# CORS (allow all in dev)
CORS_ALLOW_ALL_ORIGINS = True

# Email - SendGrid
# Pour utiliser SendGrid, définissez SENDGRID_API_KEY dans .env
import os
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

if SENDGRID_API_KEY:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.sendgrid.net"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = "apikey"
    EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
else:
    # Fallback to console if no API key
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable CSRF for easier local testing (HTMX)
# In production, ensure CSRF is properly configured
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
