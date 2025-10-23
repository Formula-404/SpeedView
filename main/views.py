from django.shortcuts import render
import requests
from django.http import JsonResponse
from datetime import datetime

def show_main(request):
    return render(request, "index.html")

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

def main_dashboard_page(request):
    """
    Menampilkan halaman dashboard utama.
    """
    return render(request, 'index.html')

def api_recent_meetings(request):
    """
    API endpoint untuk mengambil 4 meeting paling baru.
    """
    try:
        meetings_response = requests.get(f"{OPENF1_API_BASE_URL}/meetings")
        meetings_response.raise_for_status()
        all_meetings = meetings_response.json()
        all_meetings.sort(key=lambda m: m.get('date_start', ''), reverse=True)        
        recent_meetings = all_meetings[:4]
        
        return JsonResponse({'ok': True, 'data': recent_meetings})

    except requests.exceptions.RequestException as e:
        return JsonResponse({'ok': False, 'error': f"Gagal mengambil data dari OpenF1 API: {e}"}, status=500)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

def api_dashboard_data(request):
    """
    API endpoint untuk mengambil SEMUA data untuk dashboard
    berdasarkan satu meeting_key.
    """
    meeting_key = request.GET.get('meeting_key')
    if not meeting_key:
        return JsonResponse({'ok': False, 'error': 'meeting_key diperlukan'}, status=400)

    try:
        meeting_info = requests.get(f"{OPENF1_API_BASE_URL}/meetings?meeting_key={meeting_key}").json()        
        sessions = requests.get(f"{OPENF1_API_BASE_URL}/sessions?meeting_key={meeting_key}").json()
        
        race_session_key = None
        if sessions:
            for s in sessions:
                if s['session_name'].lower() == 'race':
                    race_session_key = s['session_key']
                    break
            if not race_session_key:
                race_session_key = sessions[-1]['session_key']
        
        weather_data = []
        if race_session_key:
             weather_data = requests.get(f"{OPENF1_API_BASE_URL}/weather?session_key={race_session_key}").json()

        for s in sessions:
            s['date_start_str'] = format_date(s.get('date_start'))
            s['date_end_str'] = format_date(s.get('date_end'))

        data = {
            'meeting': meeting_info[0] if meeting_info else None,
            'sessions': sessions,
            'weather': weather_data,
            'drivers': [], # Placeholder - API akan ditambahkan nanti
            'laps': [],    # Placeholder - API akan ditambahkan nanti
            'car_data': [],# Placeholder - API akan ditambahkan nanti
        }
        
        return JsonResponse({'ok': True, 'data': data})
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({'ok': False, 'error': f"Gagal mengambil data: {e}"}, status=500)


def format_date(date_string):
    """Helper untuk memformat string ISO date menjadi 'd F, H:i'"""
    if not date_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_string)
        return dt.strftime('%d %b, %H:%M')
    except (ValueError, TypeError):
        return date_string