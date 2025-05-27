import httpx
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
import asyncio
from datetime import datetime

BACKEND_URL_RECRUITMENT = "http://hiringultramyb13.duckdns.org:8080"
BACKEND_URL_LOG = "http://ec2-54-208-131-6.compute-1.amazonaws.com"

def dashboard_mahasiswa(request):
    """
    Dashboard untuk mahasiswa yang menampilkan:
    - Jumlah lowongan yang masih terbuka
    - Jumlah lowongan yang diterima  
    - Jumlah lowongan yang ditolak
    - Jumlah lowongan yang masih menunggu konfirmasi dosen
    - Jumlah jam log
    - Jumlah uang    insentif
    - Daftar seluruh lowongan yang diterima
    """

    token = request.session.get("auth_token")
    user_role = request.session.get("user_role")
    if not token:
        return redirect("authentication:login")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    context = {
        'jumlah_lowongan_terbuka': 0,
        'jumlah_lowongan_diterima': 0,
        'jumlah_lowongan_ditolak': 0,
        'jumlah_lowongan_menunggu': 0,
        'jumlah_jam_log': 0,
        'jumlah_uang_insentif': 0,
        'daftar_lowongan_diterima': [],
        'error_messages': []
    }
    
    try:
        with httpx.Client() as client:

            try:
                response_lowongan = client.get(
                    f"{BACKEND_URL_RECRUITMENT}/api/lowongan/list",
                    headers=headers,
                    timeout=10
                )
                if response_lowongan.status_code == 200:
                    all_lowongan = response_lowongan.json()
                    # Hitung lowongan yang masih terbuka
                    context['jumlah_lowongan_terbuka'] = sum(
                        1 for lowongan in all_lowongan 
                        if lowongan.get('jumlahAsistenMendaftar', 0) < lowongan.get('jumlahAsistenDibutuhkan', 0)
                    )
            except Exception as e:
                context['error_messages'].append(f"Error mengambil data lowongan: {str(e)}")

            try:
                response_logs = client.get(
                    f"{BACKEND_URL_LOG}/logs",
                    headers=headers,
                    timeout=10
                )
                if response_logs.status_code == 200:
                    logs = response_logs.json()

                    mahasiswa_logs = [log for log in logs if log.get('mahasiswaId') == request.session.get('user_id')]
     
                    context['jumlah_jam_log'] = sum(log.get('duration', 0) for log in mahasiswa_logs)
                    
                    context['jumlah_lowongan_diterima'] = sum(
                        1 for log in mahasiswa_logs if log.get('status') == 'ACCEPTED'
                    )
                    context['jumlah_lowongan_ditolak'] = sum(
                        1 for log in mahasiswa_logs if log.get('status') == 'REJECTED'
                    )
                    context['jumlah_lowongan_menunggu'] = sum(
                        1 for log in mahasiswa_logs if log.get('status') == 'PENDING'
                    )
                    
            except Exception as e:
                context['error_messages'].append(f"Error mengambil data log: {str(e)}")
        
            try:
                current_year = datetime.now().year
                current_month = datetime.now().month
                
                response_honor = client.get(
                    f"{BACKEND_URL_LOG}/dashboard/honor",
                    headers=headers,
                    params={'year': current_year, 'month': current_month},
                    timeout=10
                )
                if response_honor.status_code == 200:
                    honor_data = response_honor.json()
                    context['jumlah_uang_insentif'] = honor_data.get('totalAmount', 0)
            except Exception as e:
                context['error_messages'].append(f"Error mengambil data honor: {str(e)}")

            
    except Exception as e:
        context['error_messages'].append(f"Error koneksi: {str(e)}")
    
    return render(request, 'mahasiswa.html', context)


def daftar_lowongan(request, lowongan_id):
    """Handle pendaftaran lowongan oleh mahasiswa"""
    if request.method == 'POST':
        token = request.session.get('access_token')
        if not token:
            return redirect('login')
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        ipk = request.POST.get('ipk')
        jumlah_sks = request.POST.get('jumlah_sks')
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{BACKEND_URL_RECRUITMENT}/api/lowongan/daftar/{lowongan_id}",
                    headers=headers,
                    params={
                        'ipk': float(ipk),
                        'jumlahSks': int(jumlah_sks)
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    messages.success(request, 'Berhasil mendaftar lowongan!')
                else:
                    messages.error(request, 'Gagal mendaftar lowongan.')
                    
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('dashboard_mahasiswa')


def list_lowongan_diterima(request):
    token = request.session.get("auth_token")
    user_role = request.session.get("user_role")
    
    # Uncomment jika ingin menerapkan authentication check
    # if not token or user_role != "MAHASISWA":
    #     return redirect("authentication:login")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    context = {
        'lowongan_diterima_list': [],
        'error_message': None
    }
    
    try:
        with httpx.Client() as client:
            # Memanggil endpoint /status untuk mendapatkan lowongan yang diterima
            response = client.get(
                f"{BACKEND_URL_RECRUITMENT}/api/lowongan/status",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                context['lowongan_diterima_list'] = response.json()
            elif response.status_code == 401:
                context['error_message'] = 'Token tidak valid atau sudah expired'
            elif response.status_code == 403:
                context['error_message'] = 'Akses ditolak. Hanya mahasiswa yang dapat mengakses'
            else:
                context['error_message'] = f'Gagal mengambil data lowongan diterima (Status: {response.status_code})'
                
    except httpx.TimeoutException:
        context['error_message'] = 'Request timeout. Silakan coba lagi'
    except httpx.ConnectError:
        context['error_message'] = 'Tidak dapat terhubung ke server'
    except Exception as e:
        context['error_message'] = f'Error: {str(e)}'
    
    return render(request, 'recruitment/lamaran_diterima.html', context)

def my_logs(request):
    token = request.session.get("auth_token")
    user_role = request.session.get("user_role")
    user_id = request.session.get("user_id")

    # if not token or user_role != "MAHASISWA":
    #     return redirect("authentication:login")

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    context = {
        'logs': [],
        'error_message': None
    }

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{BACKEND_URL_LOG}/logs/{user_id}",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                context['logs'] = response.json()
            else:
                context['error_message'] = 'Gagal mengambil data log mahasiswa'

    except Exception as e:
        context['error_message'] = f'Error: {str(e)}'

    return render(request, 'log/log_list.html', context)

def dashboard_honor(request):

    token = request.session.get("auth_token")
    user_role = request.session.get("user_role")
    user_id = request.session.get("user_id")

    # if not token or user_role != "MAHASISWA":
    #     return redirect("authentication:login")

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    context = {
        'honor_details': None,
        'error_message': None
    }
    
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{BACKEND_URL_RECRUITMENT}/dashboard/honor/details",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                context['honor_details'] = response.json()
            else:
                context['error_message'] = f'Gagal mengambil data honor (Status: {response.status_code})'
                
    except Exception as e:
        context['error_message'] = f'Error: {str(e)}'
    
    return render(request, 'dashboard_mahasiswa/dashboard_honor.html', context)
