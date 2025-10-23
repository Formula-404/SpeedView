from datetime import datetime

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from apps.meeting.models import Meeting
from apps.session.models import Session

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"


def session_list(request):
    """
    Mengambil dan menampilkan daftar sesi dari API OpenF1.
    """
    sessions = []
    error = None
    try:
        params = {"meeting_key": "latest"}
        response = requests.get(f"{OPENF1_API_BASE_URL}/sessions", params=params)
        response.raise_for_status()
        sessions_data = response.json()

        for session in sessions_data:
            if session.get("date_start"):
                session["date_start"] = datetime.fromisoformat(session["date_start"])
            if session.get("date_end"):
                session["date_end"] = datetime.fromisoformat(session["date_end"])
        sessions = sorted(
            sessions_data,
            key=lambda s: s.get("date_start") or datetime.min,
            reverse=True,
        )
    except requests.exceptions.RequestException as e:
        error = f"Gagal mengambil data dari OpenF1 API: {e}"

    context = {
        "sessions": sessions,
        "error": error,
    }
    return render(request, "session_list.html", context)


@require_POST
def add_sessions(request, meeting_key: int):
    try:
        response = requests.get(
            f"{OPENF1_API_BASE_URL}/sessions",
            params={"meeting_key": meeting_key},
        )
        response.raise_for_status()
        sessions_data = response.json()
    except requests.exceptions.RequestException as exc:
        return JsonResponse(
            {"ok": False, "error": f"Gagal mengambil data sessions: {exc}"},
            status=502,
        )

    meeting_obj, _ = Meeting.objects.get_or_create(meeting_key=meeting_key)
    created = 0
    Session.objects.filter(meeting=meeting_obj).delete()

    for raw in sessions_data:
        session_key = raw.get("session_key")
        if session_key is None:
            continue
        name = raw.get("session_name") or raw.get("name") or ""
        start_time = raw.get("session_start") or raw.get("date_start") or raw.get("date")
        parsed_start = parse_datetime(start_time) if start_time else None
        Session.objects.create(
            session_key=session_key,
            meeting=meeting_obj,
            name=name,
            start_time=parsed_start,
        )
        created += 1

    return JsonResponse({"ok": True, "meeting_key": meeting_key, "created": created})
