from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('create/', views.course_create, name='course_create'),
    path('<uuid:course_id>/update/', views.course_update, name='course_update'),
    path('<uuid:course_id>/delete/', views.course_delete, name='course_delete'),
]
