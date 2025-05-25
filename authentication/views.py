# hiringgo-fe/authentication/views.py
from django.shortcuts import render, redirect
from django.contrib import messages # Untuk menampilkan pesan feedback
import requests # Untuk melakukan HTTP request
import json
from .forms import RegistrationForm, LoginForm
from django.urls import reverse

# URL Backend Spring Boot
BACKEND_URL = "http://localhost:8080/api/auth"

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            payload = {
                "namaLengkap": form.cleaned_data.get('namaLengkap'),
                "email": form.cleaned_data.get('email'),
                "password": form.cleaned_data.get('password'),
                "confirmPassword": form.cleaned_data.get('confirmPassword'),
                "role": form.cleaned_data.get('role'),
                "nim": form.cleaned_data.get('nim') if form.cleaned_data.get('role') == 'MAHASISWA' else None,
                "nip": form.cleaned_data.get('nip') if form.cleaned_data.get('role') == 'DOSEN' else None,
            }
            # Hapus key yang nilainya None agar tidak dikirim
            payload = {k: v for k, v in payload.items() if v is not None}

            try:
                response = requests.post(f"{BACKEND_URL}/register", json=payload)
                response.raise_for_status() # Akan raise HTTPError jika status code 4xx/5xx

                # Jika sukses (biasanya backend mengembalikan pesan string)
                messages.success(request, response.text) # response.text() untuk pesan dari backend
                return redirect('authentication:login') # Redirect ke halaman login setelah sukses

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400: # Bad Request dari backend
                    error_message = e.response.text # Ambil pesan error dari backend
                    messages.error(request, f"Registrasi gagal: {error_message}")
                else:
                    messages.error(request, f"Registrasi gagal: Terjadi kesalahan pada server backend (Status: {e.response.status_code}).")
            except requests.exceptions.RequestException as e:
                messages.error(request, f"Registrasi gagal: Tidak bisa terhubung ke server backend. {e}")
            except Exception as e:
                messages.error(request, f"Registrasi gagal: Terjadi kesalahan tidak terduga. {e}")
        else:
            # Form tidak valid, pesan error dari form akan ditampilkan di template
            messages.error(request, "Silakan perbaiki error pada form di bawah ini.")
    else:
        form = RegistrationForm()
    
    context = {'form': form}
    return render(request, 'register.html', context)


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            payload = {
                "email": form.cleaned_data.get('email'),
                "password": form.cleaned_data.get('password'),
            }
            try:
                response = requests.post(f"{BACKEND_URL}/login", json=payload)
                response.raise_for_status()

                # Jika sukses, backend mengembalikan JSON dengan token
                auth_data = response.json() # Konversi response ke dictionary Python
                
                # Simpan token dan data user di session Django
                request.session['auth_token'] = auth_data.get('token')
                request.session['user_email'] = auth_data.get('email')
                request.session['user_role'] = auth_data.get('role')
                request.session['user_namaLengkap'] = auth_data.get('namaLengkap')
                request.session['user_id'] = auth_data.get('userId')
                
                messages.success(request, "Login berhasil!")
                # Redirect ke halaman dashboard sesuai role (perlu dibuat nanti)
                if auth_data.get('role') == 'ADMIN':
                    return redirect('nama_app_dashboard_admin:dashboard') # Ganti dengan URL dashboard admin
                elif auth_data.get('role') == 'DOSEN':
                    return redirect(reverse("dashboard_dosen")) # Ganti dengan URL dashboard dosen
                elif auth_data.get('role') == 'MAHASISWA':
                    return redirect('nama_app_dashboard_mahasiswa:dashboard') # Ganti dengan URL dashboard mahasiswa
                else:
                    return redirect('home_page_atau_app_lain') # Halaman default jika role tidak dikenali

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401: # Unauthorized
                    messages.error(request, "Login gagal: Email atau password salah.")
                else:
                    messages.error(request, f"Login gagal: Terjadi kesalahan pada server backend (Status: {e.response.status_code}).")
            except requests.exceptions.RequestException as e:
                messages.error(request, f"Login gagal: Tidak bisa terhubung ke server backend. {e}")
            except json.JSONDecodeError:
                messages.error(request, "Login gagal: Respon dari server tidak valid.")
            except Exception as e:
                messages.error(request, f"Login gagal: Terjadi kesalahan tidak terduga. {e}")
        else:
            messages.error(request, "Silakan perbaiki error pada form di bawah ini.")
    else:
        form = LoginForm()
    
    context = {'form': form}
    return render(request, 'login.html', context)

def logout_view(request):
    # Hapus data session terkait autentikasi
    keys_to_delete = ['auth_token', 'user_email', 'user_role', 'user_namaLengkap', 'user_id']
    for key in keys_to_delete:
        if key in request.session:
            del request.session[key]
    
    messages.success(request, "Anda telah berhasil logout.")
    return redirect('authentication:login') # Redirect ke halaman login