from django.urls import path
from . import views

app_name = "visualizations"

urlpatterns = [
    path("<uuid:dataset_pk>/recommendations/", views.ChartRecommendationView.as_view(), name="recommendations"),
    path("chart/<uuid:pk>/preview/", views.ChartPreviewView.as_view(), name="chart-preview"),
    path("chart/<uuid:rec_pk>/save/", views.SaveChartView.as_view(), name="save-chart"),
    path("dashboard/<uuid:pk>/", views.DashboardView.as_view(), name="dashboard"),
]
