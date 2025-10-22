from django.shortcuts import render
from django.http import JsonResponse
import requests
from datetime import datetime
import traceback

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

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
        
        if query:
            all_meetings_response = requests.get(f"{OPENF1_API_BASE_URL}/meetings")
            all_meetings_response.raise_for_status()
            all_meetings = all_meetings_response.json()
            
            query_lower = query.lower()
            matches = [
                m for m in all_meetings 
                if query_lower in (m.get('meeting_name') or '').lower() or \
                   query_lower in (m.get('circuit_short_name') or '').lower() or \
                   query_lower in (m.get('country_name') or '').lower()
            ]
            
            if matches:
                matches.sort(key=lambda m: m.get('year') or 0, reverse=True)
                target_meeting = matches[0] # Ambil yang paling relevan/terbaru
            else:
                return JsonResponse({"ok": False, "error": f"No meeting found matching '{query}'"}, status=404)
        
        else:
            latest_meeting_response = requests.get(f"{OPENF1_API_BASE_URL}/meetings?year=latest")
            latest_meeting_response.raise_for_status()
            latest_meetings = latest_meeting_response.json()
            if latest_meetings:
                target_meeting = latest_meetings[0]
            else:
                return JsonResponse({"ok": False, "error": "No 'latest' meeting found from API"}, status=404)

        if not target_meeting or not target_meeting.get('meeting_key'):
            return JsonResponse({"ok": False, "error": "Could not determine a valid meeting."}, status=404)
        
        meeting_key = target_meeting.get('meeting_key')
        weather_response = requests.get(f"{OPENF1_API_BASE_URL}/weather?meeting_key={meeting_key}")
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        for entry in weather_data:
            if entry.get('date'):
                try:
                    entry['date'] = datetime.fromisoformat(entry['date'].replace('Z', '+00:00')).isoformat()
                except (ValueError, TypeError):
                    entry['date'] = None 

        return JsonResponse({
            "ok": True,
            "data": {
                "meeting_info": target_meeting,
                "weather_data": weather_data
            }
        })

    except requests.exceptions.RequestException as e:
        return JsonResponse({"ok": False, "error": f"Failed to fetch data from OpenF1 API: {e}"}, status=502)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"ok": False, "error": f"An unexpected server error occurred: {e}"}, status=500)