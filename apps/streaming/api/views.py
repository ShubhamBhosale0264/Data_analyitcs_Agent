"""
REST endpoint for pushing events into a stream data source.
External systems POST events here; we forward them to the Redis channel
so connected browsers receive them in real-time.
"""
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class StreamIngestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, datasource_id):
        data = request.data
        channel_layer = get_channel_layer()

        # Broadcast the event to all browsers connected to this data source's stream
        async_to_sync(channel_layer.group_send)(
            f"stream_{datasource_id}",
            {
                "type": "stream_event",  # maps to DataStreamConsumer.stream_event()
                "data": data,
                "timestamp": str(request.data.get("timestamp", "")),
            }
        )
        return Response({"status": "accepted"}, status=202)
