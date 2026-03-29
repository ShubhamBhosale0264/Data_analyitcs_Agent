import json
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from apps.datasets.models import Dataset
from .models import ChartRecommendation, SavedChart, Dashboard


class ChartRecommendationView(LoginRequiredMixin, ListView):
    """Shows all chart recommendations for a dataset, ranked by confidence."""
    model = ChartRecommendation
    template_name = "visualizations/recommendations.html"
    context_object_name = "recommendations"

    def get_queryset(self):
        self.dataset = get_object_or_404(Dataset, pk=self.kwargs["dataset_pk"])
        return ChartRecommendation.objects.filter(dataset=self.dataset)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["dataset"] = self.dataset
        return ctx


class ChartPreviewView(LoginRequiredMixin, DetailView):
    """
    Returns chart JSON for HTMX to render via Plotly.js.
    This is not a full page — it's a partial that HTMX swaps
    into the chart preview panel without a page reload.
    """
    model = ChartRecommendation
    template_name = "visualizations/partials/chart_preview.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Pass Plotly config as JSON string for the template to embed
        ctx["plotly_json"] = json.dumps(self.object.plotly_config)
        return ctx


class SaveChartView(LoginRequiredMixin, CreateView):
    model = SavedChart
    fields = ["title", "description"]
    template_name = "visualizations/save_chart.html"

    def form_valid(self, form):
        recommendation = get_object_or_404(ChartRecommendation, pk=self.kwargs["rec_pk"])
        form.instance.recommendation = recommendation
        form.instance.dataset = recommendation.dataset
        form.instance.created_by = self.request.user
        form.instance.plotly_config = recommendation.plotly_config
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, DetailView):
    model = Dashboard
    template_name = "visualizations/dashboard.html"

    def get_queryset(self):
        return Dashboard.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["dashboard_charts"] = self.object.dashboardchart_set.select_related("chart")
        return ctx
