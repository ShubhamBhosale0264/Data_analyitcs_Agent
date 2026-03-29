from rest_framework import viewsets, permissions
from apps.datasets.models import DataSource, Dataset
from .serializers import DataSourceSerializer, DatasetSerializer


class DatasetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DatasetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Dataset.objects.filter(
            source__workspace__members=self.request.user
        ).prefetch_related("columns")


class DataSourceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DataSourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DataSource.objects.filter(
            workspace__members=self.request.user
        )
