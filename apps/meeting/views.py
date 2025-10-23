import requests
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from datetime import datetime
import json

import requests
from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

def meeting_list_page(request):
    """
    Hanya merender template HTML. Data akan diambil oleh JavaScript.
    """
    return render(request, 'meeting_list.html')


def api_meeting_list(request):
    """
    API endpoint untuk mengambil data meeting dari OpenF1.
    Akan mengembalikan data dengan paginasi (10 meeting per halaman).
    """
    query = request.GET.get('q', '').strip().lower()
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    page_size = 10 # Tampilkan 10 meeting per halaman
    meetings_to_process = []
    meeting_keys: list[int] = []
    try:
        # Ambil semua meeting
        meetings_response = requests.get(f"{OPENF1_API_BASE_URL}/meetings")
        meetings_response.raise_for_status()
        all_meetings = meetings_response.json()

        # Tentukan meeting mana yang akan diproses
        if query:
            for meeting in all_meetings:
                meeting_name = meeting.get('meeting_name', '').lower()
                circuit_name = meeting.get('circuit_short_name', '').lower()
                country_name = meeting.get('country_name', '').lower()
                if query in meeting_name or query in circuit_name or query in country_name:
                    meetings_to_process.append(meeting)
        else:
            meetings_to_process = all_meetings
        
        # Urutkan agar yang terbaru muncul di atas
        meetings_to_process.sort(key=lambda m: m.get('date_start', ''), reverse=True)
        # --- LOGIKA PAGINASI ---
        total_meetings = len(meetings_to_process)
        total_pages = (total_meetings + page_size - 1) // page_size
        start_index = (page - 1) * page_size
        end_index = page * page_size
        meetings_for_this_page = meetings_to_process[start_index:end_index]

        if not meetings_for_this_page:
             return JsonResponse({'ok': True, 'data': [], 'pagination': {
                 'current_page': page, 'total_pages': total_pages, 
                 'has_previous': False, 'has_next': False, 'total_meetings': 0
             }})

        results = []
        for meeting in meetings_for_this_page:
            meeting_key_value = meeting.get('meeting_key')
            if meeting_key_value is not None:
                try:
                    meeting_keys.append(int(meeting_key_value))
                except (TypeError, ValueError):
                    pass
            meeting['date_start_str'] = format_date(meeting.get('date_start'))
            results.append(meeting)
        
        pagination_data = {
            'current_page': page,
            'total_pages': total_pages,
            'has_previous': page > 1,
            'has_next': page < total_pages,
            'total_meetings': total_meetings
        }

        return JsonResponse({'ok': True, 'data': results, 'meeting_keys': meeting_keys, 'pagination': pagination_data})
    except requests.exceptions.RequestException as e:
        return JsonResponse({'ok': False, 'error': f"Gagal mengambil data dari OpenF1 API: {e}"}, status=500)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

def format_date(date_string):
    """Helper untuk memformat string ISO date menjadi 'd F, H:i'"""
    if not date_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_string)
        return dt.strftime('%d %B')
    except (ValueError, TypeError):
        return date_string
