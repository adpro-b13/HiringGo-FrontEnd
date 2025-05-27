from django.urls import path
from . import views

app_name = 'recruitment'  # Add this line to define the application namespace

urlpatterns = [
    path('', views.lowongan_list, name='lowongan_list'),
    path('my/', views.my_lowongan, name='my_lowongan'),
    path('daftar/<int:id>/', views.daftar_lowongan, name='daftar_lowongan'),
    path('delete/<int:id>/', views.delete_lowongan, name='delete_lowongan'),
    path('create/', views.create_lowongan, name='create_lowongan'),
    path('edit/<int:id>/', views.edit_lowongan, name='edit_lowongan'),
    path('pelamar/<int:id>/', views.lihat_pelamar, name='lihat_pelamar'),
    path('pelamar/<int:pendaftaran_id>/terima/', views.terima_pelamar, name='terima_pelamar'),
    path('pelamar/<int:pendaftaran_id>/tolak/', views.tolak_pelamar, name='tolak_pelamar'),
    path('lamaran-diterima/', views.lamaran_diterima, name='lamaran_diterima'),
    path('lowongan/<int:lowongan_id>/verify-logs/', views.verify_lowongan_logs, name='verify_lowongan_logs'),
    path('log/<int:log_id>/process-verification/', views.process_log_verification, name='process_log_verification'),
]

