"""
Root URL configuration.

URL design philosophy for this project:
  /               → marketing/landing page (core app)
  /dashboard/     → main analyst dashboard (core app)
  /accounts/      → auth (allauth handles all of these)
  /datasets/      → upload, list, detail, delete
  /analysis/      → profiling results, stats, anomalies
  /viz/           → chart builder, saved charts
  /reports/       → export, download, history
  /api/v1/        → DRF REST API (used by HTMX and streaming)
  /ws/            → WebSocket (handled by Channels, see routing.py)
  /admin/         → Django admin
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # allauth handles: login, logout, signup, password reset, email confirm
    path("accounts/", include("allauth.urls")),

    # App URLs — each app owns its own urls.py
    path("", include("apps.core.urls")),
    path("datasets/", include("apps.datasets.urls")),
    path("analysis/", include("apps.analysis.urls")),
    path("viz/", include("apps.visualizations.urls")),
    path("reports/", include("apps.reports.urls")),

    # REST API — versioned so we can add v2 later without breaking clients
    path("api/v1/", include("apps.datasets.api.urls")),
    path("api/v1/", include("apps.analysis.api.urls")),
    path("api/v1/", include("apps.streaming.api.urls")),
]

# Serve uploaded files in development (in production, S3 handles this)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
