import requests
from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime
from django.db.models import Q
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from apps.meeting.models import Meeting
from apps.session.models import Session

def session_list_page(request):
    return render(request, 'session_list.html')

def api_session_list(request):
    """
    API endpoint untuk mengambil data sesi dari OpenF1.
    Akan mengembalikan sesi untuk SEMUA meeting yang ada,
    dengan paginasi (5 meeting per halaman).
    """
    query = request.GET.get('q', '').strip().lower()    
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    
    page_size = 5
    try:
        base_meetings = Meeting.objects.all()
        if query:
            base_meetings = base_meetings.filter(
                Q(circuit_short_name__icontains=query) | 
                Q(country_name__icontains=query) |
                Q(meeting_name__icontains=query)
            )
        meetings_sorted = base_meetings.order_by('-date_start')
        paginator = Paginator(meetings_sorted, page_size)
        page_obj = paginator.get_page(page)
        meetings_for_this_page = list(page_obj.object_list)
        results = []
        
        for meeting in meetings_for_this_page:
            sessions_query = Session.objects.filter(meeting_key=meeting.meeting_key).order_by('start_time')            
            sessions_data = []
            for session in sessions_query:
                sessions_data.append({
                    'session_key': session.session_key,
                    'session_name': session.name,
                    'date_start': session.start_time.isoformat() if session.start_time else None,
                    'date_start_str': format_date(session.start_time),
                    'date_end_str': '',
                })
            
            meeting_info = {
                'meeting_key': meeting.meeting_key,
                'meeting_name': meeting.meeting_name or "Unknown Meeting",
                'circuit_short_name': meeting.circuit_short_name or "Unknown Circuit",
                'country_name': meeting.country_name or "Unknown Country",
                'year': meeting.year or 2024,
            }
            
            results.append({
                'meeting_info': meeting_info,
                'sessions': sessions_data
            })
        
        pagination_data = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'total_meetings': paginator.count
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