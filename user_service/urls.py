from django.urls import path
from . import views

app_name = 'user_service'

urlpatterns = [
    path('', views.list_users, name='list_users'),
    path('create/', views.create_user, name='create_user'),
    path('update/<int:user_id>/', views.update_role, name='update_role'),
    path('delete/<int:user_id>/', views.delete_user, name='delete_user'),
]
