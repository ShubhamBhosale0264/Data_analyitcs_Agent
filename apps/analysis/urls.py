from django.urls import path
from . import views

app_name = "analysis"

urlpatterns = [
    path("<uuid:dataset_pk>/profile/", views.DataProfileView.as_view(), name="profile"),
    path("<uuid:dataset_pk>/query/", views.NLQueryView.as_view(), name="nl-query"),
    path("query/<uuid:pk>/status/", views.NLQueryStatusView.as_view(), name="nl-query-status"),
]
