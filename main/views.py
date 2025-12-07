from django.shortcuts import render
import requests
from django.http import JsonResponse
from datetime import datetime
from apps.driver.models import Driver
# views.py
from django.shortcuts import get_object_or_404
from django.core.exceptions import FieldError
from django.db.models import Prefetch
from apps.driver.models import Driver, DriverEntry
from apps.meeting.models import Meeting  # sesuaikan import path app 'meeting'

def api_dashboard_drivers_by_meeting(request):
    meeting_key = request.GET.get("meeting_key")
    if not meeting_key:
        return JsonResponse({"error": "meeting_key is required"}, status=400)

    # meeting_key bisa berupa string angka; pastikan str tetap dipakai apa adanya
    # Cari Meeting by 'meeting_key' (OpenF1). Kalau model Meeting tidak punya field itu,
    # fallback ke PK.
    try:
        meeting = Meeting.objects.get(meeting_key=meeting_key)
    except (Meeting.DoesNotExist, FieldError):
        meeting = get_object_or_404(Meeting, pk=meeting_key)

    # Ambil semua entry di meeting ini
    entries_qs = (DriverEntry.objects
                  .select_related("driver", "team")
                  .filter(meeting=meeting)
                  .order_by("driver__driver_number", "-date_start", "-id"))

    # Dedup per driver_number (loop python; aman universal untuk semua DB)
    seen = set()
    drivers = []
    for e in entries_qs:
        dn = e.driver.driver_number
        if dn in seen:
            continue
        seen.add(dn)
        d = e.driver
        # Pilih nama yang paling “siaran” buat UI
        name = d.broadcast_name or d.full_name or f"{(d.first_name or '').strip()} {(d.last_name or '').strip()}".strip()
        # Ambil warna tim dari entry kalau ada
        team_name = e.team.name if e.team else ""
        team_colour = e.team_colour or (getattr(e.team, "colour", "") if e.team else "")
        drivers.append({
            "driver_number": dn,
            "name": name,
            "acronym": d.name_acronym,
            "headshot_url": d.headshot_url,
            "team_name": team_name,
            "team_colour": team_colour,
        })

    return JsonResponse({"drivers": drivers})

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

        drivers = list(Driver.objects.all())
        data = {
            'meeting': meeting_info[0] if meeting_info else None,
            'sessions': sessions,
            'weather': weather_data,
            'drivers': [
                {
                    "driver_number": d.driver_number,
                    "full_name": d.full_name,
                    "broadcast_name": d.broadcast_name or "",
                    "headshot_url": d.headshot_url or "",
                    "country_code": d.country_code or "",
                } for d in drivers
            ],
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