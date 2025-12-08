from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.core.exceptions import FieldError
from django.db.models import Prefetch
from apps.driver.models import Driver, DriverEntry
from apps.meeting.models import Meeting  # sesuaikan import path app 'meeting'
from apps.session.models import Session
from apps.weather.models import Weather

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

def main_dashboard_page(request):
    """
    Menampilkan halaman dashboard utama.
    """
    return render(request, 'index.html')

def api_recent_meetings(request):
    """
    API endpoint untuk mengambil 4 meeting paling baru dari database lokal.
    """
    meetings = (
        Meeting.objects.all()
        .order_by("-date_start", "-meeting_key")[:4]
    )

    data = [
        {
            "meeting_key": meeting.meeting_key,
            "meeting_name": meeting.meeting_name,
            "circuit_short_name": meeting.circuit_short_name,
            "country_name": meeting.country_name,
            "year": meeting.year,
            "date_start": meeting.date_start.isoformat() if meeting.date_start else None,
        }
        for meeting in meetings
    ]

    return JsonResponse({"ok": True, "data": data})

def api_dashboard_data(request):
    """
    API endpoint untuk mengambil SEMUA data untuk dashboard
    berdasarkan satu meeting_key dari database lokal.
    """
    meeting_key = request.GET.get('meeting_key')
    if not meeting_key:
        return JsonResponse({'ok': False, 'error': 'meeting_key diperlukan'}, status=400)

    try:
        meeting_key_int = int(meeting_key)
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'meeting_key tidak valid'}, status=400)

    meeting = Meeting.objects.filter(meeting_key=meeting_key_int).first()
    if not meeting:
        return JsonResponse({'ok': False, 'error': 'meeting tidak ditemukan'}, status=404)

    sessions_qs = Session.objects.filter(meeting_key=meeting.meeting_key).order_by(
        "start_time", "session_key"
    )
    sessions: list[dict] = []
    race_session_key = None

    for session in sessions_qs:
        start_iso = session.start_time.isoformat() if session.start_time else None
        payload = {
            "session_key": session.session_key,
            "meeting_key": session.meeting_key,
            "session_name": session.name,
            "name": session.name,
            "date_start": start_iso,
            "date_end": None,
        }
        payload['date_start_str'] = format_date(start_iso)
        payload['date_end_str'] = format_date(None)
        sessions.append(payload)

        if session.name and session.name.lower() == 'race' and race_session_key is None:
            race_session_key = session.session_key

    if not race_session_key and sessions:
        race_session_key = sessions[-1]['session_key']

    weather_entries = Weather.objects.filter(meeting=meeting).order_by('date')
    weather_data = [
        {
            'meeting_key': meeting.meeting_key,
            'date': entry.date.isoformat() if entry.date else None,
            'air_temperature': entry.air_temperature,
            'track_temperature': entry.track_temperature,
            'pressure': entry.pressure,
            'wind_speed': entry.wind_speed,
            'wind_direction': entry.wind_direction,
            'humidity': entry.humidity,
            'rainfall': entry.rainfall,
        }
        for entry in weather_entries
    ]

    meeting_payload = {
        'meeting_key': meeting.meeting_key,
        'meeting_name': meeting.meeting_name,
        'circuit_short_name': meeting.circuit_short_name,
        'country_name': meeting.country_name,
        'year': meeting.year,
        'date_start': meeting.date_start.isoformat() if meeting.date_start else None,
    }

    drivers = list(Driver.objects.all())
    data = {
        'meeting': meeting_payload,
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


def format_date(date_string):
    """Helper untuk memformat string ISO date menjadi 'd F, H:i'"""
    if not date_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_string)
        return dt.strftime('%d %b, %H:%M')
    except (ValueError, TypeError):
        return date_string
