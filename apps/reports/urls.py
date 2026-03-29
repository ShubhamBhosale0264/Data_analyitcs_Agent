from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("<uuid:dataset_pk>/create/", views.ReportCreateView.as_view(), name="create"),
    path("<uuid:pk>/download/", views.ReportDownloadView.as_view(), name="download"),
]
