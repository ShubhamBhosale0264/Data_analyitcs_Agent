"""
Django Channels WebSocket consumers.

A "consumer" in Channels is the equivalent of a Django view, but for WebSocket
connections. Instead of a request/response cycle, you have connect/receive/disconnect.

Two consumers:
  1. DataStreamConsumer — pushes live dataset updates to the analyst's browser
  2. TaskProgressConsumer — pushes Celery task progress (upload, profile, report)

The channel layer (Redis) connects these consumers to the rest of the app:
  Celery task finishes a chunk → publishes to Redis channel
  → Django Channels picks it up → pushes to the browser via WebSocket
  → HTMX receives the message → swaps the progress bar partial

This means the browser never polls — it just listens. Much more efficient.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class DataStreamConsumer(AsyncWebsocketConsumer):
    """
    Pushes live data events for a specific dataset to the analyst's browser.
    Used when a DataSource is a real-time stream (Kafka / Redis Streams).
    """

    async def connect(self):
        self.dataset_id = self.scope["url_route"]["kwargs"]["dataset_id"]

        # Only allow users who have access to this dataset
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        has_access = await self.check_dataset_access(user, self.dataset_id)
        if not has_access:
            await self.close()
            return

        # Join the Redis channel group for this dataset
        # All events published to "stream_{dataset_id}" will reach this consumer
        self.group_name = f"stream_{self.dataset_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Called when a message arrives from the Redis channel group
    async def stream_event(self, event):
        """Forward a stream event from Redis to the browser."""
        await self.send(text_data=json.dumps({
            "type": "stream_event",
            "data": event["data"],
            "timestamp": event.get("timestamp"),
        }))

    @database_sync_to_async
    def check_dataset_access(self, user, dataset_id):
        from apps.datasets.models import Dataset
        return Dataset.objects.filter(
            id=dataset_id,
            source__workspace__members=user,
        ).exists()


class TaskProgressConsumer(AsyncWebsocketConsumer):
    """
    Pushes Celery task progress to the browser.
    Used by the upload progress bar, profiling progress indicator,
    and report generation status.

    Flow:
      - Analyst uploads a CSV
      - Server responds with task_id immediately
      - HTMX opens a WebSocket to /ws/tasks/{task_id}/
      - Celery task calls self.update_state(meta={"pct": 40})
      - A Celery signal publishes this to the Redis channel
      - This consumer pushes it to the browser
      - HTMX swaps the progress bar template partial
    """

    async def connect(self):
        self.task_id = self.scope["url_route"]["kwargs"]["task_id"]
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.group_name = f"task_{self.task_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def task_progress(self, event):
        """Forward task progress update to the browser."""
        await self.send(text_data=json.dumps({
            "type": "task_progress",
            "state": event["state"],
            "pct": event.get("pct", 0),
            "step": event.get("step", ""),
            "message": event.get("message", ""),
        }))

    async def task_complete(self, event):
        """Notify browser that the task finished."""
        await self.send(text_data=json.dumps({
            "type": "task_complete",
            "state": event["state"],       # SUCCESS or FAILURE
            "result": event.get("result"),
        }))
