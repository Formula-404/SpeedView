import requests
from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Meeting

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
        results = []
        for meeting in page_obj.object_list:
            meeting_key_value = meeting.meeting_key
            meeting_keys.append(int(meeting_key_value))
            results.append({
                'meeting_key': meeting.meeting_key,
                'meeting_name': meeting.meeting_name,
                'circuit_short_name': meeting.circuit_short_name,
                'country_name': meeting.country_name,
                'location': meeting.circuit_short_name,
                'year': meeting.year,
                'date_start_str': format_date(meeting.date_start),
            })
        
        pagination_data = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'total_meetings': paginator.count
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
