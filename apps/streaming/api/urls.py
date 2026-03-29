from django.urls import path
from . import views

urlpatterns = [
    path("stream/ingest/<uuid:datasource_id>/", views.StreamIngestView.as_view(), name="stream-ingest"),
]
