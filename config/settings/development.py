"""Development settings — debug toolbar, eager celery, local storage."""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
INTERNAL_IPS = ["127.0.0.1"]

# SQLite for quick local start; switch to Postgres when testing Channels/Celery
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Tasks run synchronously — no worker needed during development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
