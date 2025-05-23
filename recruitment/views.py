import httpx
import jwt
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

BACKEND_URL = "http://localhost:8081"

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
            return redirect("my_lowongan")
        else:
            return HttpResponse("Gagal menghapus lowongan", status=response.status_code)
    except Exception:
        return HttpResponse("Gagal menghubungi server", status=500)


async def lowongan_list(request):
    token = request.session.get("auth_token")
    if not token:
        return redirect("authentication:login")

    try:
        claims = jwt.decode(token, options={"verify_signature": False})
        role = claims.get("role")
    except Exception:
        return redirect("authentication:login")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BACKEND_URL}/api/lowongan/",
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

def my_lowongan(request):
    token = request.session.get("auth_token")
    if not token:
        return redirect("authentication:login")

    role = request.session.get("user_role")
    print("🟡 DEBUG: user_role from session =", role)  # 👈 this line prints the role

    if role != "DOSEN":
        return HttpResponse("Forbidden", status=403)

    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/lowongan/my",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        lowongan_list = response.json()
    except httpx.HTTPError as e:
        return HttpResponse(f"Gagal fetch data: {e}", status=500)

    return render(request, "recruitment/my_lowongan.html", {
        "lowongan_list": lowongan_list,
        "token": token
    })


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
                return redirect("my_lowongan")
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
                return redirect("my_lowongan")
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
