from django.shortcuts import render
import requests
from datetime import datetime

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

def weather_data(request):
    """
    Mengambil dan menampilkan data cuaca dari API OpenF1.
    """
    weather_entries = []
    error = None
    try:
        params = {'session_key': 'latest'} # Contoh untuk cuaca di sesi terakhir
        response = requests.get(f"{OPENF1_API_BASE_URL}/weather", params=params)
        weather_data = response.json()

        for entry in weather_data:
            if entry.get('date'):
                entry['date'] = datetime.fromisoformat(entry['date'])
        weather_entries = sorted(weather_data, key=lambda w: w.get('date') or datetime.min, reverse=True)
    except requests.exceptions.RequestException as e:
        error = f"Gagal mengambil data dari OpenF1 API: {e}"
        
    context = {
        'weather_entries': weather_entries,
        'error': error,
    }
    return render(request, 'weather_data.html', context)