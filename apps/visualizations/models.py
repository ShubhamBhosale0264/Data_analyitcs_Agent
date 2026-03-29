"""
Visualization models — stores chart configs and saved dashboards.

The core insight here: we never store chart images. We store Plotly
figure configuration (a Python dict / JSON object). The browser renders
the interactive chart from that config at display time. This means
analysts get zoom, hover, and download SVG for free, and charts
re-render correctly on any screen size.
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import UUIDModel
from apps.datasets.models import Dataset

User = get_user_model()


class ChartRecommendation(UUIDModel):
    """
    A chart type recommended by the recommendation engine for a specific dataset.
    Stores why the recommendation was made — analysts should always see the
    reasoning, not just a list of chart types.
    """
    class ChartType(models.TextChoices):
        BAR         = "bar",         "Bar Chart"
        LINE        = "line",        "Line Chart"
        SCATTER     = "scatter",     "Scatter Plot"
        HISTOGRAM   = "histogram",   "Histogram"
        HEATMAP     = "heatmap",     "Correlation Heatmap"
        BOX         = "box",         "Box Plot"
        TREEMAP     = "treemap",     "Treemap"
        PIE         = "pie",         "Pie Chart"
        AREA        = "area",        "Area Chart"

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="chart_recommendations")

    chart_type = models.CharField(max_length=30, choices=ChartType.choices)
    x_column = models.CharField(max_length=200, blank=True)
    y_column = models.CharField(max_length=200, blank=True)
    color_column = models.CharField(max_length=200, blank=True)

    # Human-readable explanation of why this chart was suggested
    reasoning = models.TextField()
    # e.g. "Region is categorical (8 values) and Revenue is numeric —
    #        a bar chart is the clearest way to compare values across categories."

    confidence_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    rank = models.IntegerField(default=1)  # 1 = top recommendation

    # Plotly config ready to render — generated on recommendation, not on page load
    plotly_config = models.JSONField(default=dict)

    generated_by = models.CharField(
        max_length=20,
        choices=[("rules", "Rule Engine"), ("ai", "AI Model")],
        default="rules"
    )

    class Meta:
        ordering = ["rank"]

    def __str__(self):
        return f"{self.chart_type} for {self.dataset.name} (rank {self.rank})"


class SavedChart(UUIDModel):
    """
    A chart that an analyst has explicitly saved to their dashboard.
    Analysts may customise the title, colors, or axis labels — those
    overrides are stored in custom_config and merged with the base config.
    """
    recommendation = models.ForeignKey(
        ChartRecommendation, on_delete=models.SET_NULL, null=True, blank=True
    )
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="saved_charts")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    plotly_config = models.JSONField(default=dict)
    custom_config = models.JSONField(default=dict)  # analyst overrides
    is_public = models.BooleanField(default=False)  # shareable link

    def __str__(self):
        return f"{self.title} (by {self.created_by})"


class Dashboard(UUIDModel):
    """
    A named collection of SavedCharts that an analyst has organised together.
    Think of it as a personal analytics report page that live-updates.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dashboards")
    charts = models.ManyToManyField(SavedChart, through="DashboardChart")
    is_shared = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True, unique=True, null=True)

    def __str__(self):
        return f"{self.name} — {self.owner.email}"


class DashboardChart(UUIDModel):
    """Through model: stores layout position of each chart on a dashboard."""
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE)
    chart = models.ForeignKey(SavedChart, on_delete=models.CASCADE)
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=6)   # out of 12 grid columns
    height = models.IntegerField(default=4)  # in grid rows

    class Meta:
        ordering = ["position_y", "position_x"]
