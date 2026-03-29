import json
from django.views.generic import DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from apps.datasets.models import Dataset
from .models import DataProfile, NLQueryResult
from .tasks import run_nl_query_task


class DataProfileView(LoginRequiredMixin, DetailView):
    """Displays the full statistical profile for a dataset."""
    model = DataProfile
    template_name = "analysis/profile_detail.html"

    def get_object(self):
        dataset = get_object_or_404(Dataset, pk=self.kwargs["dataset_pk"])
        return get_object_or_404(DataProfile, dataset=dataset)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["dataset"] = self.object.dataset
        ctx["columns"] = self.object.dataset.columns.all()
        return ctx


class NLQueryView(LoginRequiredMixin, View):
    """
    Receives a natural language question, creates an NLQueryResult record,
    kicks off the Celery task, and immediately returns the task ID.
    HTMX polls /analysis/nl-query/{id}/status/ for the result.
    """
    def post(self, request, dataset_pk):
        dataset = get_object_or_404(Dataset, pk=dataset_pk)
        data = json.loads(request.body)
        question = data.get("question", "").strip()

        if not question:
            return JsonResponse({"error": "Question cannot be empty"}, status=400)

        nl_query = NLQueryResult.objects.create(
            dataset=dataset,
            asked_by=request.user,
            question=question,
        )
        task = run_nl_query_task.delay(str(nl_query.id))
        return JsonResponse({"task_id": task.id, "query_id": str(nl_query.id)})


class NLQueryStatusView(LoginRequiredMixin, DetailView):
    """HTMX polls this for NL query results. Returns a partial template."""
    model = NLQueryResult
    template_name = "analysis/partials/nl_query_result.html"
