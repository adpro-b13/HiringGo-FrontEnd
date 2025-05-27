import httpx
from django.shortcuts import render, redirect
from django.http import HttpResponse

BACKEND_URL = "http://hiringultramyb13.duckdns.org:8080"

def dashboard_dosen_view(request):
    token = request.session.get("auth_token")
    user_role = request.session.get("user_role")

    if not token or user_role != "DOSEN" or user_role != "ADMIN":
        return redirect("authentication:login")

    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/lowongan/my",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(token)
        response.raise_for_status()
        lowongan_list = response.json()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Gagal mengambil data lowongan: {e}", status=500)

    jumlah_mata_kuliah = "Waiting for course management..."
    jumlah_mahasiswa_diterima = sum(l["jumlahAsistenDiterima"] for l in lowongan_list)
    jumlah_lowongan_terbuka = sum(
        1 for l in lowongan_list if l["jumlahAsistenDiterima"] < l["jumlahAsistenDibutuhkan"]
    )

    context = {
        "jumlah_mata_kuliah": jumlah_mata_kuliah,
        "jumlah_mahasiswa_diterima": jumlah_mahasiswa_diterima,
        "jumlah_lowongan_terbuka": jumlah_lowongan_terbuka
    }

    return render(request, "dashboard_dosen/dashboard.html", context)
