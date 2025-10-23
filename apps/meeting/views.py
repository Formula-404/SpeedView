from datetime import datetime

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from apps.meeting.models import Meeting

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"


def meeting_list(request):
    """
    Mengambil dan menampilkan daftar meeting dari API OpenF1.
    """
    meetings = []
    error = None
    try:
        response = requests.get(f"{OPENF1_API_BASE_URL}/meetings")
        response.raise_for_status()
        meetings_data = response.json()
        for meeting in meetings_data:
            if meeting.get("date_start"):
                meeting["date_start"] = datetime.fromisoformat(
                    meeting["date_start"]
                )
        meetings = sorted(
            meetings_data,
            key=lambda m: m.get("date_start") or datetime.min,
            reverse=True,
        )
    except requests.exceptions.RequestException as e:
        error = f"Gagal mengambil data dari OpenF1 API: {e}"

    context = {
        "meetings": meetings,
        "error": error,
    }
    return render(request, "meeting_list.html", context)


@require_POST
def add_meetings(request):
    try:
        response = requests.get(f"{OPENF1_API_BASE_URL}/meetings")
        response.raise_for_status()
        meetings_data = response.json()
    except requests.exceptions.RequestException as exc:
        return JsonResponse(
            {"ok": False, "error": f"Gagal mengambil data meetings: {exc}"},
            status=502,
        )

    created = 0
    for meeting in meetings_data:
        key = meeting.get("meeting_key")
        if key is None:
            continue
        _, was_created = Meeting.objects.get_or_create(meeting_key=key)
        if was_created:
            created += 1

    return JsonResponse({"ok": True, "created": created})
