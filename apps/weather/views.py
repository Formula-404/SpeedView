from django.shortcuts import render
from django.http import JsonResponse
import traceback
from django.db.models import Q
from apps.meeting.models import Meeting
from .models import Weather

def weather_list_page(request):
    """
    Hanya merender kerangka halaman HTML. Data akan dimuat oleh JavaScript.
    """
    return render(request, 'weather/weather_list.html')

def api_weather_list(request):
    """
    API endpoint untuk mengambil data cuaca untuk meeting tertentu.
    Ini akan mencari meeting berdasarkan query, atau mengambil yang terbaru.
    """
    query = request.GET.get('q', None)
    
    try:
        target_meeting = None
        base_query = Meeting.objects.all().order_by('-date_start')
        if query:
            query_lower = query.lower()
            matches = base_query.filter(
                Q(meeting_name__icontains=query_lower) |
                Q(circuit_short_name__icontains=query_lower) |
                Q(country_name__icontains=query_lower)
            )
            
            if matches.exists():
                target_meeting = matches.first()
            else:
                return JsonResponse({"ok": False, "error": f"No meeting found matching '{query}'"}, status=44)
        
        else:
            target_meeting = base_query.first()
            if not target_meeting:
                return JsonResponse({"ok": False, "error": "No 'latest' meeting found in database"}, status=404)

        weather_query = Weather.objects.filter(meeting=target_meeting).order_by('date')        
        weather_data = []
        for entry in weather_query:
            weather_data.append({
                'date': entry.date.isoformat(),
                'air_temperature': entry.air_temperature,
                'track_temperature': entry.track_temperature,
                'pressure': entry.pressure,
                'wind_speed': entry.wind_speed,
                'wind_direction': entry.wind_direction,
                'humidity': entry.humidity,
                'rainfall': entry.rainfall,
            })

        meeting_info = {
            'meeting_key': target_meeting.meeting_key,
            'meeting_name': target_meeting.meeting_name,
            'circuit_short_name': target_meeting.circuit_short_name,
            'country_name': target_meeting.country_name,
            'year': target_meeting.year,
        }

        return JsonResponse({"ok": True, "data": {"meeting_info": meeting_info, "weather_data": weather_data}})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"ok": False, "error": f"An unexpected server error occurred: {e}"})