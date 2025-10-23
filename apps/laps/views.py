# apps/laps/views.py
import requests
from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

# ---------- Page ----------
def laps_list_page(request):
    return render(request, "laps_list.html")  # buat template sederhana seperti session_list.html

def lap_detail_page(request, driver_number):   # disesuaikan dengan link di UI
    return render(request, "lap_detail.html", {"driver_number": driver_number})

# ---------- Helpers ----------
def _fmt(dt):
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt).strftime("%d %b, %H:%M")
    except Exception:
        return dt

def _get(params):
    r = requests.get(f"{OPENF1_API_BASE_URL}/laps", params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    for row in data:
        row["date_start_str"] = _fmt(row.get("date_start"))
    return data

# ---------- API ----------
def api_laps_list(request):
    # Meneruskan filter yang ada di OpenF1: session_key, driver_number, lap_number, meeting_key
    params = {}
    for key in ("session_key", "driver_number", "lap_number", "meeting_key"):
        val = request.GET.get(key)
        if val:
            params[key] = val
    try:
        data = _get(params)
        return JsonResponse({"ok": True, "count": len(data), "data": data})
    except requests.RequestException as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=502)
 