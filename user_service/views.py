from django.shortcuts import render, redirect
from django.http import HttpResponse
import httpx

BACKEND_URL = "http://13.55.205.168:8081/api/v1/user"
TOKEN_HEADER = lambda token: {"Authorization": f"Bearer {token}"}

def admin_required(view_fn):
    def _wrapped(request, *args, **kwargs):
        # 1. Cek udah login (punya token di session)
        if not request.session.get('auth_token'):
            return redirect('authentication:login')
        # 2. Cek role ADMIN
        if request.session.get('user_role') != 'ADMIN':
            return HttpResponse("Forbidden", status=403)
        return view_fn(request, *args, **kwargs)
    return _wrapped

@admin_required
def list_users(request):
    token = request.session.get('auth_token')
    resp = httpx.get(f"{BACKEND_URL}/list", headers=TOKEN_HEADER(token))
    users = resp.json().get('users', [])
    return render(request, "list.html", {"users": users})

@admin_required
def create_user(request):
    token = request.session.get('auth_token')
    if request.method == "POST":
        payload = {
            "namaLengkap": request.POST['namaLengkap'],
            "email": request.POST['email'],
            "role": request.POST['role'],
            "password": request.POST['password'],
            "nim": request.POST.get('nim'),
            "nip": request.POST.get('nip'),
        }
        resp = httpx.post(f"{BACKEND_URL}/create", headers=TOKEN_HEADER(token), json=payload)
        if resp.status_code == 201:
            return redirect('user_service:list_users')
        else:
            return HttpResponse(f"Gagal: {resp.text}", status=resp.status_code)
    return render(request, "create.html")

@admin_required
def update_role(request, user_id):
    token = request.session.get('auth_token')
    if request.method == "POST":
        new_role = request.POST['role']
        resp = httpx.patch(f"{BACKEND_URL}/update-role/{user_id}", headers=TOKEN_HEADER(token), json={"role": new_role})
        if resp.status_code == 200:
            return redirect('user_service:list_users')
        else:
            return HttpResponse(f"Gagal: {resp.text}", status=resp.status_code)
    # get current user untuk form
    resp = httpx.get(f"{BACKEND_URL}/{user_id}", headers=TOKEN_HEADER(token))
    user = resp.json()
    return render(request, "update.html", {"user": user})

@admin_required
def delete_user(request, user_id):
    token = request.session.get('auth_token')
    resp = httpx.delete(f"{BACKEND_URL}/delete/{user_id}", headers=TOKEN_HEADER(token))
    return redirect('user_service:list_users')
