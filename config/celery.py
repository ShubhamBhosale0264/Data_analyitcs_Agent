"""
Celery application configuration.

Why a separate file instead of putting this in settings?
Celery needs to be imported BEFORE Django apps load (for autodiscovery),
so keeping it isolated here avoids circular import issues.
"""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("analytics_platform")

# Pull Celery config from Django settings (any key starting with CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in every installed app
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
