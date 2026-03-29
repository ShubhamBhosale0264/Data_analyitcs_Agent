from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class LandingView(TemplateView):
    template_name = "core/landing.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main analyst dashboard — shows recent datasets, analyses, and quick stats.
    LoginRequiredMixin redirects to LOGIN_URL if user isn't authenticated.
    """
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # These will be populated once other apps are built
        ctx["recent_datasets"] = []
        ctx["recent_analyses"] = []
        return ctx
