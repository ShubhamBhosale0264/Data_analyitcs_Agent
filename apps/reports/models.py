"""
Reports app — manages export jobs and stores generated report files.

Report generation (especially PDF with embedded charts) can take 30-60 seconds
for large datasets. It always runs as a Celery task, never blocking the web process.
Analysts get a download link emailed/notified to them when the report is ready.
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import UUIDModel
from apps.datasets.models import Dataset

User = get_user_model()


class Report(UUIDModel):
    class ReportType(models.TextChoices):
        PDF   = "pdf",   "PDF Report"
        EXCEL = "excel", "Excel Workbook"

    class Status(models.TextChoices):
        QUEUED     = "queued",     "Queued"
        GENERATING = "generating", "Generating"
        READY      = "ready",      "Ready"
        FAILED     = "failed",     "Failed"

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="reports")
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    report_type = models.CharField(max_length=10, choices=ReportType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    title = models.CharField(max_length=200)
    include_profile = models.BooleanField(default=True)
    include_charts = models.BooleanField(default=True)
    include_anomalies = models.BooleanField(default=True)
    include_nl_queries = models.BooleanField(default=False)

    # The generated file (stored in media/reports/)
    output_file = models.FileField(upload_to="reports/%Y/%m/", null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    generation_time_seconds = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    celery_task_id = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.title} ({self.report_type}) — {self.status}"
