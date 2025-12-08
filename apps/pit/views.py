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
    # filter utama
    filters = {}
    for key in ("session_key", "driver_number", "lap_number", "meeting_key"):
        val = request.GET.get(key)
        if val:
            filters[key] = val

    # parameter pagination
    try:
        limit = int(request.GET.get("limit", "20"))
    except ValueError:
        limit = 20
    try:
        offset = int(request.GET.get("offset", "0"))
    except ValueError:
        offset = 0

    if limit <= 0:
        limit = 20
    if offset < 0:
        offset = 0

    try:
        r = requests.get(
            f"{OPENF1_API_BASE_URL}/pit", params=filters or None, timeout=20
        )
        r.raise_for_status()
        data = r.json()
        for row in data:
            row["date_str"] = _fmt(row.get("date"))

        total = len(data)
        start = offset
        end = offset + limit
        sliced = data[start:end]

        has_more = end < total
        next_offset = end if has_more else None

        return JsonResponse(
            {
                "ok": True,
                "count": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "has_more": has_more,
                "data": sliced,
            }
        )
    except requests.RequestException as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=502)
