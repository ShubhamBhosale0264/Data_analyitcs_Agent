"""
Analysis models — stores the results of every analytical operation.

Key design decision: results are stored in the DB as JSON, not recomputed
on every page load. This means: (a) the analysis page loads instantly,
(b) analysts can compare results across time if data is refreshed,
(c) the LLM narrative is only generated once (expensive API call).
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import UUIDModel
from apps.datasets.models import Dataset

User = get_user_model()


class DataProfile(UUIDModel):
    """
    The full statistical profile of a dataset — generated once after ingestion,
    updated if the dataset is refreshed.

    Stores the heavy ydata-profiling output as JSON rather than as normalized
    DB rows, because the shape of profiling results varies per column type.
    JSON is the right tradeoff here: flexible, fast to write, readable in admin.
    """
    dataset = models.OneToOneField(Dataset, on_delete=models.CASCADE, related_name="profile")
    generated_by_task = models.CharField(max_length=200, blank=True)

    # Raw profiling data (from ydata-profiling or our custom engine)
    profile_data = models.JSONField(default=dict)
    # Structure: {"columns": {...per-col stats...}, "correlations": {...}, "missing": {...}}

    # Pre-computed insights the LLM or rule engine extracted
    key_insights = models.JSONField(default=list)
    # [{"type": "high_correlation", "cols": ["A","B"], "value": 0.92, "text": "..."}, ...]

    # LLM-generated plain-English narrative summary
    ai_narrative = models.TextField(blank=True)
    ai_narrative_generated_at = models.DateTimeField(null=True, blank=True)

    # Quality scores (0-100)
    completeness_score = models.FloatField(null=True)  # % non-null values
    consistency_score = models.FloatField(null=True)   # type consistency
    uniqueness_score = models.FloatField(null=True)    # duplication assessment

    def __str__(self):
        return f"Profile for {self.dataset.name}"


class CorrelationMatrix(UUIDModel):
    """
    Stores pairwise column correlations for the dataset.
    Kept separate from DataProfile because analysts may want to view or
    filter correlations independently, and the matrix can be large.
    """
    dataset = models.OneToOneField(Dataset, on_delete=models.CASCADE, related_name="correlation_matrix")
    method = models.CharField(max_length=20, default="pearson")  # pearson | spearman | cramers_v
    matrix_data = models.JSONField(default=dict)  # {"col_A": {"col_B": 0.87, "col_C": -0.23}}
    strong_correlations = models.JSONField(default=list)  # pairs above threshold (|r| > 0.7)

    def __str__(self):
        return f"Correlations for {self.dataset.name}"


class AnomalyReport(UUIDModel):
    """
    Records anomalous rows detected by the outlier detection engine.
    Analysts can view flagged rows, dismiss false positives, and export
    just the anomalies for investigation.
    """
    class DetectionMethod(models.TextChoices):
        ISOLATION_FOREST = "isolation_forest", "Isolation Forest (multivariate)"
        ZSCORE           = "zscore",           "Z-Score (univariate)"
        IQR              = "iqr",              "Interquartile Range"

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="anomaly_reports")
    method = models.CharField(max_length=30, choices=DetectionMethod.choices)
    contamination_rate = models.FloatField(default=0.05)  # expected % of outliers
    anomaly_count = models.IntegerField(default=0)
    anomaly_indices = models.JSONField(default=list)  # row indices flagged as anomalies
    feature_importance = models.JSONField(default=dict)  # which columns drove the detection
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Anomalies in {self.dataset.name} ({self.anomaly_count} found)"


class NLQueryResult(UUIDModel):
    """
    Stores the result of a natural language query — the question, the generated
    SQL, the execution result, and the chart config.

    Storing NL query history serves two purposes:
    1. Analysts can revisit past queries without re-typing them
    2. You can build a query suggestion engine from the most common questions
    """
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="nl_queries")
    asked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # The raw question the analyst typed
    question = models.TextField()

    # What the LLM generated (always show this to the analyst for transparency)
    generated_sql = models.TextField(blank=True)
    sql_explanation = models.TextField(blank=True)  # LLM explains what the SQL does

    # Execution results
    result_data = models.JSONField(default=list)   # [{col: val}, ...] row dicts
    result_row_count = models.IntegerField(default=0)
    execution_time_ms = models.IntegerField(default=0)
    execution_error = models.TextField(blank=True)

    # Chart config generated for the result
    chart_config = models.JSONField(default=dict)  # Plotly figure dict

    # LLM provider and model used (for cost tracking and debugging)
    llm_provider = models.CharField(max_length=50, blank=True)
    llm_model = models.CharField(max_length=100, blank=True)
    llm_tokens_used = models.IntegerField(default=0)

    was_successful = models.BooleanField(default=False)

    def __str__(self):
        return f'"{self.question[:50]}..." on {self.dataset.name}'
