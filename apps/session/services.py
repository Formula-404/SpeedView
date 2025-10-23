import logging
from typing import Iterable

import requests
from django.utils.dateparse import parse_datetime

from apps.meeting.models import Meeting
from apps.session.models import Session


LOGGER = logging.getLogger(__name__)
OPENF1_SESSIONS_URL = "https://api.openf1.org/v1/sessions"


def ensure_sessions_for_meetings(
    meetings: Iterable[int | Meeting],
    *,
    timeout: float = 10.0,
) -> dict[int, dict[str, int]]:
    meeting_list = list(meetings)
    if not meeting_list:
        return {}

    meeting_keys: list[int] = []
    for item in meeting_list:
        if isinstance(item, Meeting):
            meeting_key = item.meeting_key
        else:
            meeting_key = getattr(item, "meeting_key", item)
        if meeting_key is None:
            continue
        try:
            meeting_keys.append(int(meeting_key))
        except (TypeError, ValueError):
            continue

    meeting_keys = sorted(set(meeting_keys))
    if not meeting_keys:
        return {}

    present_meetings = set(
        Session.objects.filter(meeting_key__in=meeting_keys).values_list(
            "meeting_key", flat=True
        )
    )

    results: dict[int, dict[str, int]] = {}

    # Fetch sessions only for meetings that do not yet have any rows.
    for meeting_key in meeting_keys:
        if meeting_key in present_meetings:
            continue

        try:
            response = requests.get(
                OPENF1_SESSIONS_URL,
                params={"meeting_key": meeting_key},
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.warning(
                "Failed to pull sessions for meeting %s: %s",
                meeting_key,
                exc,
            )
            continue

        try:
            payload = response.json()
        except ValueError as exc:
            LOGGER.warning(
                "Invalid JSON when pulling sessions for meeting %s: %s",
                meeting_key,
                exc,
            )
            continue

        if not isinstance(payload, list):
            LOGGER.warning(
                "Unexpected payload when pulling sessions for meeting %s: %r",
                meeting_key,
                payload,
            )
            continue

        created = 0
        updated = 0

        # Preload existing sessions referenced by the payload.
        session_key_values: set[int] = set()
        for row in payload:
            value = row.get("session_key")
            if value is None:
                continue
            try:
                session_key_values.add(int(value))
            except (TypeError, ValueError):
                continue

        existing_sessions = {
            session.session_key: session
            for session in Session.objects.filter(session_key__in=session_key_values)
        }

        for row in payload:
            try:
                session_key = int(row["session_key"])
            except (KeyError, TypeError, ValueError):
                continue

            name = row.get("session_name") or row.get("name") or ""
            start_time_raw = (
                row.get("date_start")
                or row.get("session_start")
                or row.get("date")
            )
            start_time = parse_datetime(start_time_raw) if start_time_raw else None

            session = existing_sessions.get(session_key)
            if session is None:
                session = Session.objects.create(
                    session_key=session_key,
                    meeting_key=meeting_key,
                    name=name,
                    start_time=start_time,
                )
                existing_sessions[session_key] = session
                created += 1
                continue

            update_fields: list[str] = []

            if session.meeting_key != meeting_key:
                session.meeting_key = meeting_key
                update_fields.append("meeting_key")

            if name and session.name != name:
                session.name = name
                update_fields.append("name")

            if start_time and session.start_time != start_time:
                session.start_time = start_time
                update_fields.append("start_time")

            if update_fields:
                session.save(update_fields=update_fields)
                updated += 1

        results[meeting_key] = {"created": created, "updated": updated}

    return results
