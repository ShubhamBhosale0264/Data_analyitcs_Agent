from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("workspace/create/", views.WorkspaceCreateView.as_view(), name="workspace-create"),
    path("workspace/<slug:slug>/", views.WorkspaceDetailView.as_view(), name="workspace-detail"),
    path("workspace/<slug:slug>/invite/", views.InviteMemberView.as_view(), name="invite-member"),
]
