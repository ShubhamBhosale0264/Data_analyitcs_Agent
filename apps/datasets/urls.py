from django.urls import path
from . import views

app_name = "datasets"

urlpatterns = [
    path("", views.DatasetListView.as_view(), name="list"),
    path("upload/", views.DatasetUploadView.as_view(), name="upload"),
    path("<uuid:pk>/", views.DatasetDetailView.as_view(), name="detail"),
    path("<uuid:pk>/status/", views.TaskStatusView.as_view(), name="task-status"),
]
