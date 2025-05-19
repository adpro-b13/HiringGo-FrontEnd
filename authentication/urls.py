# hiringgo-fe/authentication/urls.py
from django.urls import path
from . import views # Kita akan membuat views.py nanti

app_name = 'authentication' # Namespace untuk URL (sangat direkomendasikan!)

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
]