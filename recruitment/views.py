import httpx
import jwt
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

BACKEND_URL = "http://hiringultramyb13.duckdns.org:8080"
BACKEND_URL_LOG = "http://ec2-54-208-131-6.compute-1.amazonaws.com" # Added for log service

def delete_lowongan(request, id):
    if request.method != "POST":
        return HttpResponse(status=405)

    token = request.POST.get("token")
    try:
        response = httpx.delete(
            f"{BACKEND_URL}/api/lowongan/delete/{id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            return redirect("recruitment:my_lowongan")
        else:
            return HttpResponse("Gagal menghapus lowongan", status=response.status_code)
    except Exception:
        return HttpResponse("Gagal menghubungi server", status=500)

def lamaran_diterima(request):
    token = request.session.get("auth_token")
    if not token:
        return redirect("authentication:login")

    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/lowongan/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        lamaran_list = response.json()
        print("🟢 Lamaran List JSON:", lamaran_list)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponse(f"🔥 Internal Error: {e}", status=500)

    return render(request, "recruitment/lamaran_diterima.html", {
        "lamaran_list": lamaran_list
    })




def lowongan_list(request):
    token = request.session.get("auth_token")
    if not token:
        return redirect("authentication:login")

    try:
        claims = jwt.decode(token, options={"verify_signature": False})
        role = claims.get("roles")
        print(token)
        print(role)
        print("🔥 lowongan_list view was called")
    except Exception:
        return redirect("authentication:login")

    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/lowongan/list",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        lowongan_list = response.json()
    except httpx.HTTPError:
        return HttpResponse("Failed to fetch lowongan", status=500)

    return render(request, "recruitment/lowongan_list.html", {
        "lowongan_list": lowongan_list,
        "role": role,
        "token": token
    })


@csrf_exempt
def daftar_lowongan(request, id):
    if request.method != "POST":
        return HttpResponse(status=405)

    token = request.POST.get("token")
    ipk = request.POST.get("ipk")
    jumlah_sks = request.POST.get("jumlahSks")

    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/lowongan/daftar/{id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"ipk": ipk, "jumlahSks": jumlah_sks},
        )
        if response.status_code == 200:
            return redirect("lowongan_list")
        else:
            return HttpResponse("Gagal mendaftar ke lowongan", status=response.status_code)
    except Exception:
        return HttpResponse("Gagal menghubungi server", status=500)

@csrf_exempt
def my_lowongan(request):
    token = request.session.get("auth_token")
    if not token:
        return redirect("authentication:login")

    role = request.session.get("user_role")
    print("🟡 DEBUG: user_role from session =", role)

    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/lowongan/my",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("🟢 Status code:", response.status_code)
        print("🟢 Response text:", response.text)
        response.raise_for_status()
        lowongan_list = response.json()
        print("✅ Parsed JSON:", lowongan_list)
        print(token)

    except httpx.HTTPStatusError as e:
        print("❌ HTTP error:", e)
        print("❌ Response body:", e.response.text)
        return HttpResponse(f"Gagal fetch data: {e}", status=e.response.status_code)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponse(f"🔥 Internal Django Error: {str(e)}", status=500)

    return render(request, "recruitment/my_lowongan.html", {
        "lowongan_list": lowongan_list,
        "token": token
    })

@csrf_exempt
def terima_pelamar(request, pendaftaran_id):
    token = request.session.get("auth_token")
    if not token:
        return redirect("authentication:login")

    try:
        response = httpx.put(
            f"{BACKEND_URL}/api/lowongan/pelamar/{pendaftaran_id}/terima",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return redirect(request.META.get("HTTP_REFERER", "my_lowongan"))
        else:
            return HttpResponse("Gagal menerima pelamar", status=response.status_code)
    except Exception:
        return HttpResponse("Gagal menghubungi server", status=500)

@csrf_exempt
def tolak_pelamar(request, pendaftaran_id):
    token = request.session.get("auth_token")
    if not token:
        return redirect("authentication:login")

    try:
        response = httpx.put(
            f"{BACKEND_URL}/api/lowongan/pelamar/{pendaftaran_id}/tolak",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return redirect(request.META.get("HTTP_REFERER", "my_lowongan"))
        else:
            return HttpResponse("Gagal menolak pelamar", status=response.status_code)
    except Exception:
        return HttpResponse("Gagal menghubungi server", status=500)


@csrf_exempt
def edit_lowongan(request, id):
    token = request.session.get("auth_token")
    if not token:
        return redirect("authentication:login")

    if request.method == "POST":
        mata_kuliah = request.POST.get("mataKuliah")
        semester = request.POST.get("semester")
        tahun_ajaran = request.POST.get("tahunAjaran")
        jumlah = request.POST.get("jumlahAsistenDibutuhkan")

        try:
            response = httpx.put(
                f"{BACKEND_URL}/api/lowongan/edit/{id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "mataKuliah": mata_kuliah,
                    "semester": semester,
                    "tahunAjaran": tahun_ajaran,
                    "jumlahAsistenDibutuhkan": int(jumlah)
                }
            )
            if response.status_code == 200:
                return redirect("recruitment:my_lowongan")
            else:
                return HttpResponse("Gagal mengedit lowongan", status=response.status_code)
        except Exception:
            return HttpResponse("Gagal menghubungi server", status=500)

    response = httpx.get(
        f"{BACKEND_URL}/api/lowongan/{id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    lowongan = response.json()
    return render(request, "recruitment/edit_lowongan.html", {"lowongan": lowongan})

@csrf_exempt
def create_lowongan(request):
    token = request.session.get("auth_token")
    if not token:
        return redirect("authentication:login")

    if request.method == "POST":
        mata_kuliah = request.POST.get("mataKuliah")
        semester = request.POST.get("semester")
        tahun_ajaran = request.POST.get("tahunAjaran")
        jumlah = request.POST.get("jumlahAsistenDibutuhkan")

        try:
            response = httpx.post(
                f"{BACKEND_URL}/api/lowongan/create",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "mataKuliah": mata_kuliah,
                    "semester": semester,
                    "tahunAjaran": tahun_ajaran,
                    "jumlahAsistenDibutuhkan": int(jumlah)
                }
            )
            if response.status_code == 200:
                return redirect("recruitment:my_lowongan")
            else:
                return HttpResponse("Gagal membuat lowongan", status=response.status_code)
        except Exception:
            return HttpResponse("Gagal menghubungi server", status=500)

    return render(request, "recruitment/create_lowongan.html")

def lihat_pelamar(request, id):
    token = request.session.get("auth_token")
    user_role = request.session.get("user_role")

    if not token:
        return redirect("authentication:login")

    if user_role != "DOSEN":
        return HttpResponse("Forbidden", status=403)

    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/lowongan/pelamar/{id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            pelamar_list = response.json()
        elif response.status_code == 403:
            return HttpResponse("Anda bukan pembuat lowongan ini.", status=403)
        else:
            return HttpResponse("Gagal mengambil data pelamar", status=response.status_code)
    except Exception:
        return HttpResponse("Gagal menghubungi server", status=500)

    return render(request, "recruitment/pelamar_list.html", {
        "pelamar_list": pelamar_list,
        "lowongan_id": id
    })

@csrf_exempt
def verify_lowongan_logs(request, lowongan_id):
    token = request.session.get("auth_token")
    user_role = request.session.get("user_role")

    if not token:
        return redirect("authentication:login")
    if user_role != "DOSEN":
        return HttpResponse("Forbidden: Hanya Dosen yang dapat mengakses halaman ini.", status=403)

    headers = {"Authorization": f"Bearer {token}"}
    logs_to_verify = []
    error_message = None

    try:
        # Fetch lowongan details to display its name or title
        lowongan_detail_response = httpx.get(
            f"{BACKEND_URL}/api/lowongan/{lowongan_id}",
            headers=headers
        )
        lowongan_detail_response.raise_for_status()
        lowongan = lowongan_detail_response.json()

        # Fetch logs for this lowongan that need verification
        response = httpx.get(
            f"{BACKEND_URL_LOG}/logs/lecturer",
            headers=headers,
            params={"vacancyId": lowongan_id}
        )
        response.raise_for_status()
        logs_to_verify = response.json()
    except httpx.HTTPStatusError as e:
        error_message = f"Gagal mengambil data: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        error_message = f"Gagal menghubungi server: {str(e)}"
    except Exception as e:
        error_message = f"Terjadi kesalahan: {str(e)}"

    return render(request, "recruitment/verify_page.html", {
        "logs": logs_to_verify,
        "lowongan": lowongan,
        "lowongan_id": lowongan_id,
        "token": token,
        "error_message": error_message
    })

@csrf_exempt
def process_log_verification(request, log_id):
    token = request.session.get("auth_token")
    user_role = request.session.get("user_role")

    if not token:
        return redirect("authentication:login")
    if user_role != "DOSEN":
        return HttpResponse("Forbidden: Hanya Dosen yang dapat melakukan aksi ini.", status=403)

    if request.method == "POST":
        action = request.POST.get("action") # "ACCEPT" or "REJECT"
        # lowongan_id_for_redirect = request.POST.get("lowongan_id") # Get lowongan_id from hidden input

        if not action:
            return HttpResponse("Aksi tidak valid.", status=400)

        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = httpx.post(
                f"{BACKEND_URL_LOG}/logs/{log_id}/verify",
                headers=headers,
                params={"action": action.upper()}
            )
            response.raise_for_status()
            verified_log_data = response.json()
            lowongan_id_for_redirect = verified_log_data.get("vacancyId")

            if lowongan_id_for_redirect:
                return redirect(reverse('verify_lowongan_logs', kwargs={'lowongan_id': lowongan_id_for_redirect}))
            else:
                # Fallback if vacancyId is not in response, though it should be.
                # This might lead to an error or redirect to a generic page.
                return redirect(request.META.get("HTTP_REFERER", "my_lowongan"))

        except httpx.HTTPStatusError as e:
            # Handle error, maybe show a message
            return HttpResponse(f"Gagal memproses verifikasi log: {e.response.status_code} - {e.response.text}", status=e.response.status_code)
        except Exception as e:
            return HttpResponse(f"Terjadi kesalahan saat verifikasi: {str(e)}", status=500)
    
    return HttpResponse("Metode tidak diizinkan.", status=405)
