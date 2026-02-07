"""
Test settings.
"""
import os
from .base import *  # noqa: F401, F403

DEBUG = False

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use PostgreSQL in CI, SQLite locally
if os.environ.get("DATABASE_URL"):
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.config(conn_max_age=600)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# Disable cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Use database sessions for tests (instead of cache-based which requires Redis)
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Email
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Celery (eager execution)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
