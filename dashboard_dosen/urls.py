from django.urls import path
from .views import dashboard_dosen_view

urlpatterns = [
    path('', dashboard_dosen_view, name='dashboard_dosen'),
]
