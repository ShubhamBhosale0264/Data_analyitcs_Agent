"""
Dataset models — the central domain of the entire application.

Every analyst interaction (profiling, charting, NL query, export) starts
here. These models must be designed carefully because changing them later
requires data migrations that can be painful.

Key design decision: DataSource is the connection config (where does data
come from?). Dataset is a specific snapshot or table from that source.
This lets analysts connect one Postgres database (DataSource) and work
with many tables from it (Dataset × N), without re-entering credentials.
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import UUIDModel
from apps.accounts.models import Workspace

User = get_user_model()


class DataSource(UUIDModel):
    """
    Represents a connection to an external data origin.
    Think of this as the 'connector' — the credentials and config
    needed to reach the raw data.
    """
    class SourceType(models.TextChoices):
        FILE    = "file",    "File Upload (CSV/Excel)"
        SQL     = "sql",     "SQL Database"
        STREAM  = "stream",  "Real-time Stream"
        API     = "api",     "REST API"  # reserved for future phase

    name = models.CharField(max_length=200)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="data_sources")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)

    # SQL connector config — only populated when source_type == "sql"
    # WARNING: connection_string contains credentials. Encrypt at rest in production.
    # Use django-fernet-fields for automatic field-level encryption.
    connection_string = models.TextField(blank=True, help_text="SQLAlchemy connection string")
    db_schema = models.CharField(max_length=100, blank=True, default="public")

    # Stream config — only for source_type == "stream"
    stream_topic = models.CharField(max_length=200, blank=True)
    stream_config = models.JSONField(default=dict, blank=True)
    # e.g. {"bootstrap_servers": "kafka:9092", "group_id": "analytics"}

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class Dataset(UUIDModel):
    """
    A specific table, file, or stream snapshot ready for analysis.
    This is what analysts actually work with — a concrete, queryable set of data.

    The relationship to DataSource: one DataSource (a Postgres connection)
    can produce many Datasets (one per table the analyst chooses to import).
    """
    class Status(models.TextChoices):
        PENDING    = "pending",    "Pending"      # just uploaded, not yet processed
        PROCESSING = "processing", "Processing"   # Celery task running
        READY      = "ready",      "Ready"        # profiling done, ready for analysis
        ERROR      = "error",      "Error"        # processing failed
        ARCHIVED   = "archived",   "Archived"     # soft-deleted

    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="datasets")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Raw file location (for file uploads) — points to S3 key or local path
    file = models.FileField(upload_to="datasets/raw/%Y/%m/", null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)

    # For SQL sources: which table/view was imported
    table_name = models.CharField(max_length=200, blank=True)
    sql_query = models.TextField(blank=True, help_text="Custom SQL query if not using full table")

    # Cached metadata (populated after processing, avoids re-reading file every time)
    row_count = models.BigIntegerField(null=True, blank=True)
    column_count = models.IntegerField(null=True, blank=True)
    schema_snapshot = models.JSONField(default=dict, blank=True)
    # schema_snapshot format: {"col_name": {"dtype": "float64", "semantic": "currency", "null_pct": 0.02}}

    # Processed data stored as parquet (much faster to read than CSV)
    parquet_path = models.CharField(max_length=500, blank=True)

    # Celery task tracking
    processing_task_id = models.CharField(max_length=200, blank=True)
    processing_error = models.TextField(blank=True)
    last_refreshed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.row_count or '?'} rows)"

    @property
    def is_ready(self):
        return self.status == self.Status.READY


class Column(UUIDModel):
    """
    Metadata about one column in a Dataset.

    Storing column metadata in the DB (not re-derived from the file each time)
    is what makes the chart recommender and NL query engine fast.
    They query Column objects — no pandas required at request time.
    """
    class DataType(models.TextChoices):
        INTEGER  = "integer",  "Integer"
        FLOAT    = "float",    "Float"
        STRING   = "string",   "String / Text"
        BOOLEAN  = "boolean",  "Boolean"
        DATETIME = "datetime", "Date / Time"
        UNKNOWN  = "unknown",  "Unknown"

    class SemanticType(models.TextChoices):
        """
        Semantic types go beyond the raw dtype to describe what the data MEANS.
        A column might be dtype=float but semantic=currency — that changes which
        charts and aggregations make sense for it.
        """
        IDENTIFIER  = "id",       "Identifier / Key"
        CURRENCY    = "currency", "Currency / Money"
        PERCENTAGE  = "pct",      "Percentage"
        CATEGORY    = "category", "Category / Label"
        DATE        = "date",     "Date"
        TIMESTAMP   = "ts",       "Timestamp"
        GEOGRAPHY   = "geo",      "Geography / Location"
        FREE_TEXT   = "text",     "Free Text"
        NUMERIC     = "numeric",  "General Numeric"
        UNKNOWN     = "unknown",  "Unknown"

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="columns")
    name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200, blank=True)  # analyst-friendly label
    position = models.IntegerField(default=0)  # column order in the original file

    # Types
    data_type = models.CharField(max_length=20, choices=DataType.choices, default=DataType.UNKNOWN)
    semantic_type = models.CharField(max_length=20, choices=SemanticType.choices, default=SemanticType.UNKNOWN)

    # Basic profiling stats (stored here for fast access without re-reading data)
    null_count = models.BigIntegerField(default=0)
    null_percentage = models.FloatField(default=0.0)
    unique_count = models.BigIntegerField(default=0)
    unique_percentage = models.FloatField(default=0.0)
    sample_values = models.JSONField(default=list)  # up to 10 example values

    # Numeric stats (null for non-numeric columns)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    mean_value = models.FloatField(null=True, blank=True)
    std_value = models.FloatField(null=True, blank=True)
    median_value = models.FloatField(null=True, blank=True)

    # Categorical stats (null for numeric columns)
    top_values = models.JSONField(default=dict)
    # e.g. {"UK": 4521, "US": 3890, "DE": 1203}

    is_target_candidate = models.BooleanField(default=False)   # likely ML target variable
    is_feature_candidate = models.BooleanField(default=False)  # good ML feature

    class Meta:
        ordering = ["position"]
        unique_together = ("dataset", "name")

    def __str__(self):
        return f"{self.dataset.name}.{self.name} ({self.data_type})"
