# hiringgo-fe/authentication/views.py
from django.shortcuts import render
from django.http import HttpResponse

def login_view(request):
    return render(request, 'login.html')

def register_view(request):
    return render(request, 'register.html')