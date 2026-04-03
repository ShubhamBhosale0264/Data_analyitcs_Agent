from django.urls import path
from .views import LandingView, DashboardView

app_name = 'core'

urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]