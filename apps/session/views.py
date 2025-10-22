from django.shortcuts import render
import requests
from datetime import datetime

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
        sessions_data = response.json()

        for session in sessions_data:
            if session.get('date_start'):
                session['date_start'] = datetime.fromisoformat(session['date_start'])
            if session.get('date_end'):
                session['date_end'] = datetime.fromisoformat(session['date_end'])
        sessions = sorted(sessions_data, key=lambda s: s.get('date_start') or datetime.min, reverse=True)
    except requests.exceptions.RequestException as e:
        error = f"Gagal mengambil data dari OpenF1 API: {e}"
        
    context = {
        'sessions': sessions,
        'error': error,
    }
    return render(request, 'session_list.html', context)
