from rest_framework import serializers
from apps.datasets.models import DataSource, Dataset, Column


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ["id", "name", "display_name", "data_type", "semantic_type",
                  "null_percentage", "unique_count", "mean_value", "top_values"]


class DatasetSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Dataset
        fields = ["id", "name", "description", "status", "status_display",
                  "row_count", "column_count", "columns", "created_at"]


class DataSourceSerializer(serializers.ModelSerializer):
    datasets = DatasetSerializer(many=True, read_only=True)

    class Meta:
        model = DataSource
        fields = ["id", "name", "source_type", "description", "datasets", "created_at"]
        # Deliberately exclude connection_string — never expose credentials via API
