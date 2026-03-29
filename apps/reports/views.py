from django.views.generic import CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from .models import Report
from .tasks import generate_pdf_report_task, generate_excel_report_task


class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    fields = ["report_type", "title", "include_profile", "include_charts", "include_anomalies"]
    template_name = "reports/report_create.html"

    def form_valid(self, form):
        from apps.datasets.models import Dataset
        dataset = get_object_or_404(Dataset, pk=self.kwargs["dataset_pk"])
        form.instance.dataset = dataset
        form.instance.requested_by = self.request.user
        response = super().form_valid(form)

        if self.object.report_type == Report.ReportType.PDF:
            task = generate_pdf_report_task.delay(str(self.object.id))
        else:
            task = generate_excel_report_task.delay(str(self.object.id))

        self.object.celery_task_id = task.id
        self.object.save(update_fields=["celery_task_id"])
        return response


class ReportDownloadView(LoginRequiredMixin, DetailView):
    model = Report

    def get(self, request, *args, **kwargs):
        report = self.get_object()
        if report.status != Report.Status.READY:
            raise Http404("Report is not ready yet.")
        return FileResponse(
            report.output_file.open("rb"),
            as_attachment=True,
            filename=report.output_file.name.split("/")[-1],
        )
