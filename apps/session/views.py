from django.shortcuts import render
import requests

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

def session_list(request):
    """
    Mengambil dan menampilkan daftar sesi dari API OpenF1.
    """
    sessions = []
    error = None
    try:
        params = {'meeting_key': 'latest'} # Contoh untuk mendapatkan sesi dari meeting terakhir
        response = requests.get(f"{OPENF1_API_BASE_URL}/sessions", params=params)
        response.raise_for_status()
        sessions = response.json()
    except requests.exceptions.RequestException as e:
        error = f"Gagal mengambil data dari OpenF1 API: {e}"
        
    context = {
        'sessions': sessions,
        'error': error,
    }
    return render(request, 'session/session_list.html', context)
