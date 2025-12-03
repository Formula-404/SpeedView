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
    """
    Panggil OpenF1 /laps dengan fallback default bila params kosong.
    Di sini TIDAK ada parameter limit/offset: pagination ditangani Django.
    """
    q = {k: v for k, v in (params or {}).items() if v not in ("", None)}
    if not q:
        # default lama yang sudah bekerja di proyek kamu
        q = {"meeting_key": "latest"}

    r = requests.get(f"{OPENF1_API_BASE_URL}/laps", params=q, timeout=20)
    r.raise_for_status()
    data = r.json()
    for row in data:
        row["date_start_str"] = _fmt(row.get("date_start"))
    return data


def api_laps_list(request):
    # filter utama
    filters = {}
    for key in ("session_key", "driver_number", "lap_number", "meeting_key"):
        val = request.GET.get(key)
        if val:
            filters[key] = val

    # parameter pagination dari *frontend*
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
        data = _fetch_laps(filters)
        total = len(data)

        start = offset
        end = offset + limit
        sliced = data[start:end]

        has_more = end < total
        next_offset = end if has_more else None

        return JsonResponse(
            {
                "ok": True,
                "count": total,          # total semua data untuk filter tsb
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "has_more": has_more,
                "data": sliced,          # hanya potongan sesuai limit/offset
            }
        )
    except requests.HTTPError as e:
        try:
            status = e.response.status_code
        except Exception:
            status = 502
        msg = f"{status} Client Error: {getattr(e.response, 'reason', str(e))}"
        if not filters:
            msg += (
                " (endpoint /laps butuh minimal satu filter; "
                "kami sarankan meeting_key atau session_key)"
            )
        return JsonResponse({"ok": False, "error": msg}, status=502)
    except requests.RequestException as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=502)
