
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lowongan_list, name='lowongan_list'),
    path('my/', views.my_lowongan, name='my_lowongan'),
    path('daftar/<int:id>/', views.daftar_lowongan, name='daftar_lowongan'),
    path('delete/<int:id>/', views.delete_lowongan, name='delete_lowongan'),
    path('create/', views.create_lowongan, name='create_lowongan'),
    path('edit/<int:id>/', views.edit_lowongan, name='edit_lowongan'),
    path('pelamar/<int:id>/', views.lihat_pelamar, name='lihat_pelamar'),
]

