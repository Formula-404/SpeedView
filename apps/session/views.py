import requests
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from datetime import datetime
import json

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

def session_list_page(request):
    """
    Hanya merender template HTML. Data akan diambil oleh JavaScript.
    """
    return render(request, 'session_list.html')


def api_session_list(request):
    """
    API endpoint untuk mengambil data sesi dari OpenF1.
    Akan mengembalikan sesi untuk SEMUA meeting yang ada,
    dengan paginasi (10 meeting per halaman).
    """
    query = request.GET.get('q', '').strip().lower()    
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    
    page_size = 5
    meetings_to_process = []
    try:
        # Ambil semua meeting
        meetings_response = requests.get(f"{OPENF1_API_BASE_URL}/meetings")
        meetings_response.raise_for_status()
        all_meetings = meetings_response.json()

        # Tentukan meeting mana yang akan diproses
        if query:
            for meeting in all_meetings:
                circuit_name = meeting.get('circuit_short_name', '').lower()
                country_name = meeting.get('country_name', '').lower()
                if query in circuit_name or query in country_name:
                    meetings_to_process.append(meeting)
        else:
            meetings_to_process = all_meetings
        
        # Urutkan agar yang terbaru muncul di atas
        meetings_to_process.sort(key=lambda m: m.get('date_start', ''), reverse=True)
        # --- LOGIKA PAGINASI BARU ---
        total_meetings = len(meetings_to_process)
        total_pages = (total_meetings + page_size - 1) // page_size # Kalkulasi total halaman
        # Ambil potongan 5 meeting untuk halaman saat ini
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
            meeting_key = meeting['meeting_key']
            params = {'meeting_key': meeting_key}
            response = requests.get(f"{OPENF1_API_BASE_URL}/sessions", params=params)
            if not response.ok:
                print(f"Gagal mengambil sesi untuk meeting_key: {meeting_key}")
                continue 
                
            sessions_data = response.json()  
            for session in sessions_data:
                session['date_start_str'] = format_date(session.get('date_start'))
                session['date_end_str'] = format_date(session.get('date_end'))
            
            results.append({
                'meeting_info': meeting,
                'sessions': sessions_data
            })
        
        pagination_data = {
            'current_page': page,
            'total_pages': total_pages,
            'has_previous': page > 1,
            'has_next': page < total_pages,
            'total_meetings': total_meetings
        }
        return JsonResponse({'ok': True, 'data': results, 'pagination': pagination_data})
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
        return dt.strftime('%d %b, %H:%M')
    except (ValueError, TypeError):
        return date_string