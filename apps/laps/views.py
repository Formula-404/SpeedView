import requests
from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

def laps_list_page(request):
    return render(request, "laps_list.html")

def lap_detail_page(request, driver_number):
    return render(request, "laps_list.html", {"driver_number": driver_number})

def _fmt(dt):
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt).strftime("%d %b, %H:%M")
    except Exception:
        return dt

def _fetch_laps(params: dict):
    """Panggil OpenF1 /laps dengan fallback default bila params kosong."""
    q = {k: v for k, v in (params or {}).items() if v not in ("", None)}
    if not q:
        q = {"meeting_key": "latest"}
    r = requests.get(f"{OPENF1_API_BASE_URL}/laps", params=q, timeout=20)
    r.raise_for_status()
    data = r.json()
    for row in data:
        row["date_start_str"] = _fmt(row.get("date_start"))
    return data

def api_laps_list(request):
    params = {}
    for key in ("session_key", "driver_number", "lap_number", "meeting_key"):
        val = request.GET.get(key)
        if val:
            params[key] = val
    try:
        data = _fetch_laps(params)
        return JsonResponse({"ok": True, "count": len(data), "data": data})
    except requests.HTTPError as e:
        try:
            status = e.response.status_code
        except Exception:
            status = 502
        msg = f"{status} Client Error: {getattr(e.response, 'reason', str(e))}"
        if not params:
            msg += " (endpoint /laps butuh minimal satu filter; kami sarankan meeting_key atau session_key)"
        return JsonResponse({"ok": False, "error": msg}, status=502)
    except requests.RequestException as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=502)
