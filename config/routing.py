"""
ASGI URL routing — handles both HTTP and WebSocket connections.
Django Channels intercepts WS upgrade requests here before they
reach the normal Django URL router.
"""
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.streaming.consumers import DataStreamConsumer, TaskProgressConsumer

# Two WebSocket endpoints:
#   /ws/stream/{dataset_id}/  — live data stream updates for a dataset
#   /ws/tasks/{task_id}/      — Celery task progress (e.g. profiling 67% done)
websocket_urlpatterns = [
    re_path(r"ws/stream/(?P<dataset_id>[^/]+)/$", DataStreamConsumer.as_asgi()),
    re_path(r"ws/tasks/(?P<task_id>[^/]+)/$", TaskProgressConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
