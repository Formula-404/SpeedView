from django.shortcuts import render
import requests

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

def meeting_list(request):
    """
    Mengambil dan menampilkan daftar meeting dari API OpenF1.
    """
    meetings = []
    error = None
    try:
        response = requests.get(f"{OPENF1_API_BASE_URL}/meetings")
        response.raise_for_status()
        meetings = response.json()
    except requests.exceptions.RequestException as e:
        error = f"Gagal mengambil data dari OpenF1 API: {e}"
        
    context = {
        'meetings': meetings,
        'error': error,
    }
    return render(request, 'meeting/meeting_list.html', context)