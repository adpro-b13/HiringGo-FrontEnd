from django.urls import path
from .views import dashboard_admin_view

app_name = 'dashboard_admin'

urlpatterns = [
    path('', dashboard_admin_view, name='dashboard_admin'),
]
