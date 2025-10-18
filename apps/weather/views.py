from django.shortcuts import render
import requests

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
        response.raise_for_status()
        weather_entries = response.json()
    except requests.exceptions.RequestException as e:
        error = f"Gagal mengambil data dari OpenF1 API: {e}"
        
    context = {
        'weather_entries': weather_entries,
        'error': error,
    }
    return render(request, 'weather/weather_data.html', context)