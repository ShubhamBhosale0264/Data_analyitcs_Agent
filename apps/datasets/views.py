"""
Dataset views — handle file upload, list, detail, and deletion.

Views are deliberately thin. They delegate:
  - Data processing → Celery tasks
  - Business logic → model methods or service functions
  - Rendering → templates (with HTMX for partial updates)
"""
import logging
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import DataSource, Dataset
from .tasks import ingest_file_task

logger = logging.getLogger(__name__)


class DatasetListView(LoginRequiredMixin, ListView):
    model = Dataset
    template_name = "datasets/dataset_list.html"
    context_object_name = "datasets"
    paginate_by = 20

    def get_queryset(self):
        # Only show datasets belonging to workspaces this user is a member of
        return Dataset.objects.filter(
            source__workspace__members=self.request.user
        ).select_related("source", "source__workspace")


class DatasetDetailView(LoginRequiredMixin, DetailView):
    model = Dataset
    template_name = "datasets/dataset_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["columns"] = self.object.columns.all()
        ctx["analyses"] = self.object.analyses.all()[:5]
        return ctx


class DatasetUploadView(LoginRequiredMixin, CreateView):
    """
    Handles CSV/Excel file upload.
    On valid form submission: saves the file, triggers the Celery ingest task,
    and immediately redirects — the analyst sees a progress indicator via HTMX.
    """
    model = Dataset
    template_name = "datasets/dataset_upload.html"
    fields = ["name", "description", "file"]

    def form_valid(self, form):
        # We need to create the DataSource and Dataset objects first
        # This would typically use a form wizard or multi-step form
        response = super().form_valid(form)

        # Kick off async processing — don't block the HTTP response
        task = ingest_file_task.delay(str(self.object.id))
        self.object.processing_task_id = task.id
        self.object.save(update_fields=["processing_task_id"])

        messages.info(self.request, f"'{self.object.name}' is being processed. We'll notify you when it's ready.")
        logger.info(f"Ingest task {task.id} queued for dataset {self.object.id}")
        return response

    def get_success_url(self):
        return reverse_lazy("datasets:detail", kwargs={"pk": self.object.pk})


class TaskStatusView(LoginRequiredMixin, DetailView):
    """
    HTMX polls this endpoint every second to get task progress.
    Returns a partial HTML template (not a full page) so HTMX can
    swap just the progress bar component without reloading anything.
    """
    model = Dataset
    template_name = "datasets/partials/task_progress.html"

    def get_context_data(self, **kwargs):
        from celery.result import AsyncResult
        ctx = super().get_context_data(**kwargs)
        if self.object.processing_task_id:
            result = AsyncResult(self.object.processing_task_id)
            ctx["task_state"] = result.state
            ctx["task_info"] = result.info or {}
        return ctx
