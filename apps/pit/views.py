import requests
from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

def pit_list_page(request):
    return render(request, "pit_list.html")

def pit_detail_page(request, driver_number):  
    return render(request, "pit_detail.html", {"driver_number": driver_number})

def _fmt(dt):
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt).strftime("%d %b, %H:%M")
    except Exception:
        return dt

def api_pit_list(request):
    params = {}
    for key in ("session_key", "driver_number", "lap_number", "meeting_key"):
        val = request.GET.get(key)
        if val:
            params[key] = val
    try:
        r = requests.get(f"{OPENF1_API_BASE_URL}/pit", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        for row in data:
            row["date_str"] = _fmt(row.get("date"))
        return JsonResponse({"ok": True, "count": len(data), "data": data})
    except requests.RequestException as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=502)
