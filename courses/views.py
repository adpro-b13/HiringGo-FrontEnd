from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
import requests

BACKEND_URL = 'http://localhost:8080/admin/matakuliah'

def course_list(request):
    try:
        response = requests.get(f'{BACKEND_URL}/list')
        response.raise_for_status()
        courses = response.json()
    except Exception as e:
        courses = []
        messages.error(request, f'Gagal mengambil data: {e}')
    return render(request, 'courses/course_list.html', {'courses': courses})

def course_create(request):
    if request.method == 'POST':
        lecturer_names = request.POST.get('lecturers', '')
        dosen_pengampu = []
        if lecturer_names:
            for name in [n.strip() for n in lecturer_names.split(',') if n.strip()]:
                dosen_pengampu.append({'nama': name})
        data = {
            'kode': request.POST.get('kode'),
            'nama': request.POST.get('nama'),
            'deskripsi': request.POST.get('deskripsi'),
            'dosenPengampu': dosen_pengampu
        }
        try:
            response = requests.post(f'{BACKEND_URL}/add', json=data)
            response.raise_for_status()
            messages.success(request, 'Mata kuliah berhasil dibuat!')
            return redirect(reverse('courses:course_list'))
        except Exception as e:
            messages.error(request, f'Gagal membuat mata kuliah: {e}')
    return render(request, 'courses/course_create.html')

def course_update(request, course_id):
    try:
        response = requests.get(f'{BACKEND_URL}/{course_id}')
        response.raise_for_status()
        course = response.json()
    except Exception as e:
        messages.error(request, f'Gagal mengambil data: {e}')
        return redirect(reverse('courses:course_list'))
    if request.method == 'POST':
        lecturer_names = request.POST.get('lecturers', '')
        dosen_pengampu = []
        if lecturer_names:
            for name in [n.strip() for n in lecturer_names.split(',') if n.strip()]:
                dosen_pengampu.append({'nama': name})
        data = {
            'kode': course['kode'],
            'nama': request.POST.get('nama'),
            'deskripsi': request.POST.get('deskripsi'),
            'dosenPengampu': dosen_pengampu
        }
        try:
            response = requests.put(f'{BACKEND_URL}/{course_id}', json=data)
            response.raise_for_status()
            messages.success(request, 'Mata kuliah berhasil diupdate!')
            return redirect(reverse('courses:course_list'))
        except Exception as e:
            messages.error(request, f'Gagal update: {e}')
            # Update course object with POSTed data for re-render
            course['nama'] = request.POST.get('nama')
            course['deskripsi'] = request.POST.get('deskripsi')
            course['dosenPengampu'] = dosen_pengampu
    return render(request, 'courses/course_update.html', {'course': course})

def course_delete(request, course_id):
    try:
        response = requests.delete(f'{BACKEND_URL}/{course_id}')
        response.raise_for_status()
        messages.success(request, 'Mata kuliah berhasil dihapus!')
    except Exception as e:
        messages.error(request, f'Gagal menghapus: {e}')
    return redirect(reverse('courses:course_list'))
