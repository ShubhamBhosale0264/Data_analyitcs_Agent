from django.urls import path
from . import views

urlpatterns = [
    path("analysis/<uuid:dataset_pk>/profile/", views.DataProfileAPIView.as_view(), name="api-profile"),
    path("analysis/<uuid:dataset_pk>/query/", views.NLQueryAPIView.as_view(), name="api-nl-query"),
]
