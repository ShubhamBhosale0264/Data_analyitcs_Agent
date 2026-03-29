from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("datasets", views.DatasetViewSet, basename="dataset")
router.register("sources", views.DataSourceViewSet, basename="datasource")

urlpatterns = [path("", include(router.urls))]
