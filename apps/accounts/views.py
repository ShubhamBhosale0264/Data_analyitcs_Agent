from django.views.generic import DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Workspace, WorkspaceMembership


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = "accounts/profile.html"
    fields = ["first_name", "last_name", "bio", "avatar"]
    success_url = reverse_lazy("accounts:profile")

    def get_object(self):
        return self.request.user


class WorkspaceCreateView(LoginRequiredMixin, CreateView):
    model = Workspace
    template_name = "accounts/workspace_form.html"
    fields = ["name", "slug", "description"]

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        # Auto-add creator as admin member
        WorkspaceMembership.objects.create(
            workspace=self.object,
            user=self.request.user,
            role=WorkspaceMembership.Role.ADMIN,
        )
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


class WorkspaceDetailView(LoginRequiredMixin, DetailView):
    model = Workspace
    template_name = "accounts/workspace_detail.html"
    slug_field = "slug"


class InviteMemberView(LoginRequiredMixin, CreateView):
    model = WorkspaceMembership
    template_name = "accounts/invite_member.html"
    fields = ["user", "role"]

    def form_valid(self, form):
        workspace = Workspace.objects.get(slug=self.kwargs["slug"])
        form.instance.workspace = workspace
        form.instance.invited_by = self.request.user
        return super().form_valid(form)
