from django.urls import path
from . import views

urlpatterns = [

    path('dashboard/mahasiswa/', views.dashboard_mahasiswa, name='dashboard_mahasiswa'),

    path('lowongan/diterima/', views.list_lowongan_diterima, name='list_lowongan_diterima'),
    path('lowongan/daftar/<int:lowongan_id>/', views.daftar_lowongan, name='daftar_lowongan'),
  
    path('logs/my/', views.my_logs, name='my_logs'),
    

]