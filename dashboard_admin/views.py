import asyncio
import httpx
from asgiref.sync import sync_to_async
from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse

USER_SERVICE_URL        = "http://13.55.205.168:8081/api/v1/user"
COURSES_SERVICE_URL     = "http://localhost:8080/admin/matakuliah"
RECRUITMENT_SERVICE_URL = "http://hiringultramyb13.duckdns.org:8080/api/lowongan"

async def dashboard_admin_view(request):
    # ambil token & role secara async
    token = await sync_to_async(request.session.get)('auth_token')
    role  = await sync_to_async(request.session.get)('user_role')
    if not token or role != 'ADMIN':
        return redirect('authentication:login')

    headers = {"Authorization": f"Bearer {token}"}

    # helper async untuk fetch masing‐masing service
    async def fetch_users(client):
        try:
            resp = await client.get(f"{USER_SERVICE_URL}/list", headers=headers, timeout=5.0)
            resp.raise_for_status()
            users = resp.json().get('users', [])
            dosen     = sum(1 for u in users if u.get('role') == 'DOSEN')
            mahasiswa = sum(1 for u in users if u.get('role') == 'MAHASISWA')
            return dosen, mahasiswa
        except Exception as e:
            await sync_to_async(messages.error)(request, f"[Users] gagal: {e}")
            return 0, 0

    async def fetch_courses(client):
        try:
            resp = await client.get(f"{COURSES_SERVICE_URL}/list", headers=headers, timeout=5.0)
            resp.raise_for_status()
            return len(resp.json())
        except Exception as e:
            await sync_to_async(messages.error)(request, f"[Courses] gagal: {e}")
            return 0

    async def fetch_lowongan(client):
        try:
            resp = await client.get(f"{RECRUITMENT_SERVICE_URL}/list", headers=headers, timeout=5.0)
            resp.raise_for_status()
            return len(resp.json())
        except Exception as e:
            await sync_to_async(messages.error)(request, f"[Lowongan] gagal: {e}")
            return 0

    # jalankan ketiganya secara bersamaan
    async with httpx.AsyncClient() as client:
        task_users   = asyncio.create_task(fetch_users(client))
        task_courses = asyncio.create_task(fetch_courses(client))
        task_lowong  = asyncio.create_task(fetch_lowongan(client))

        jumlah_dosen, jumlah_mahasiswa = await task_users
        jumlah_mata_kuliah             = await task_courses
        jumlah_lowongan                = await task_lowong

    context = {
        'jumlah_dosen': jumlah_dosen,
        'jumlah_mahasiswa': jumlah_mahasiswa,
        'jumlah_mata_kuliah': jumlah_mata_kuliah,
        'jumlah_lowongan': jumlah_lowongan,
    }
    # pakai TemplateResponse untuk async view
    return TemplateResponse(request, 'dashboard_admin/dashboard.html', context)
