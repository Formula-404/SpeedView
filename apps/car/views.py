import datetime
import json
from collections import defaultdict
from functools import wraps
from typing import Dict, Iterable, List, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from apps.car.forms import CarForm
from apps.car.models import Car
from apps.meeting.models import Meeting
from apps.session.models import Session


import json
from typing import List, Dict

def _loads_json_array_best_effort(payload: bytes | str) -> List[Dict]:
    if isinstance(payload, (bytes, bytearray)):
        text = payload.decode("utf-8", errors="replace")
    else:
        text = payload

    dec = json.JSONDecoder()
    i = 0
    n = len(text)

    while i < n and text[i].isspace():
        i += 1
    if i >= n or text[i] != "[":
        return []

    i += 1  
    out: List[Dict] = []

    while i < n:
        while i < n and text[i] in " \t\r\n,":
            i += 1
        if i >= n:
            break
        if text[i] == "]":
            break  

        try:
            obj, j = dec.raw_decode(text, i)
        except json.JSONDecodeError:
            break

        out.append(obj)
        i = j

    return out


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        is_admin = getattr(request.user, "is_superuser", False) or getattr(
            profile, "role", None
        ) == "admin"
        if not is_admin:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "message": "Admin access required."}, status=403
                )
            raise PermissionDenied("Admin access required.")
        return view_func(request, *args, **kwargs)
    return login_required(_wrapped, login_url="/login")


@login_required(login_url="/login")
def show_main(request):
    return redirect("car:list_page")


def _extract_meeting_key(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        key = getattr(value, "meeting_key", None)
        return int(key) if key is not None else None
    except (TypeError, ValueError):
        return None


def _coerce_int_or_none(value) -> int | None:
    if value in (None, "", "None"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_meeting_key_from_session(session_key: int | None) -> int | None:
    if session_key is None:
        return None
    session_obj = Session.objects.filter(session_key=session_key).first()
    if session_obj and session_obj.meeting_key is not None:
        try:
            return int(session_obj.meeting_key)
        except (TypeError, ValueError):
            return None
    return None


def _collect_extra_meeting_keys(
    data,
    *,
    existing_car: Car | None = None,
) -> list[int]:
    keys: list[int] = []
    meeting_value = _coerce_int_or_none(data.get("meeting_key"))
    session_value = _coerce_int_or_none(data.get("session_key"))
    if meeting_value is not None:
        keys.append(meeting_value)
    linked_from_session = _resolve_meeting_key_from_session(session_value)
    if linked_from_session is not None:
        keys.append(linked_from_session)

    if existing_car is not None:
        if existing_car.meeting_key is not None:
            keys.append(int(existing_car.meeting_key))
        if existing_car.session_key is not None:
            linked_existing = _resolve_meeting_key_from_session(
                existing_car.session_key
            )
            if linked_existing is not None:
                keys.append(linked_existing)

    deduped = sorted({value for value in keys if value is not None})
    return deduped


def _meeting_choices_for_payload(data, *, existing_car: Car | None = None):
    extra_keys = _collect_extra_meeting_keys(data, existing_car=existing_car)
    meeting_choices = _fetch_meeting_choices(extra_keys=extra_keys or None)
    return meeting_choices


def _compute_session_offset_seconds(car: Car) -> int | None:
    session_obj = getattr(car, "session_obj", None)
    if session_obj is None and car.session_key is not None:
        session_obj = Session.objects.filter(session_key=car.session_key).first()
    if not session_obj or not session_obj.start_time or not car.date:
        return None
    delta = car.date - session_obj.start_time
    return max(0, int(delta.total_seconds()))


def _build_session_catalog(meetings: Iterable[int]) -> dict[str, List[dict[str, str]]]:
    meeting_keys = []
    for item in meetings:
        key = _extract_meeting_key(item)
        if key is not None:
            meeting_keys.append(key)
    meeting_keys = sorted(set(meeting_keys))
    catalog: dict[str, List[dict[str, str]]] = {str(key): [] for key in meeting_keys}

    if not meeting_keys:
        return catalog

    sessions = Session.objects.filter(meeting_key__in=meeting_keys).order_by(
        "meeting_key", "session_key"
    )

    for session in sessions:
        if session.meeting_key is None:
            continue
        catalog.setdefault(str(session.meeting_key), []).append(
            {
                "value": session.session_key,
                "label": str(session),
            }
        )

    return catalog


@admin_required
def add_car(request):
    meeting_choices = _fetch_meeting_choices()
    meeting_keys = [choice[0] for choice in meeting_choices]
    form = CarForm(request.POST or None, meeting_choices=meeting_choices)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        if form.is_valid():
            car_entry = form.save()

            payload = {
                "success": True,
                "message": "Car telemetry added.",
                "car": serialize_car(car_entry),
            }
            if is_ajax:
                return JsonResponse(payload, status=201)

            messages.success(request, "Car telemetry added.")
            return redirect("car:manual_list")

        if is_ajax:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

        messages.error(request, "Please correct the errors below.")

    session_catalog = _build_session_catalog(meeting_keys)

    return render(
        request,
        "add_car.html",
        {
            "form": form,
            "session_catalog": session_catalog,
        },
    )


def show_car(request, id):
    car = get_object_or_404(Car, pk=id)
    return render(request, "car_detail.html", {"car": car})


@admin_required
@require_POST
@csrf_exempt
def add_car_entry_ajax(request):
    meeting_choices = _meeting_choices_for_payload(request.POST)
    form = CarForm(request.POST, meeting_choices=meeting_choices)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    car = form.save()

    return JsonResponse(
        {
            "success": True,
            "message": "Car telemetry entry created successfully.",
            "car": serialize_car(car),
        },
        status=201,
    )


@admin_required
@require_POST
@csrf_exempt
def update_car_entry_ajax(request, car_id: int):
    car = get_object_or_404(Car, pk=car_id, is_manual=True)
    meeting_choices = _meeting_choices_for_payload(request.POST, existing_car=car)
    form = CarForm(request.POST, instance=car, meeting_choices=meeting_choices)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    updated_car = form.save()

    return JsonResponse(
        {
            "success": True,
            "message": "Car telemetry entry updated successfully.",
            "car": serialize_car(updated_car),
        }
    )


@admin_required
@require_POST
@csrf_exempt
def delete_car_entry_ajax(request, car_id: int):
    car = get_object_or_404(Car, pk=car_id, is_manual=True)
    deleted_id = car.id
    car.delete()
    return JsonResponse(
        {
            "success": True,
            "deleted_id": deleted_id,
        }
    )


@login_required(login_url="/login")
def show_xml(request):
    car_list = Car.objects.all()
    xml_data = serializers.serialize("xml", car_list)
    return HttpResponse(xml_data, content_type="application/xml")


@login_required(login_url="/login")
def show_json(request):
    try:
        limit = int(request.GET.get("limit", 500))
    except (TypeError, ValueError):
        limit = 500
    limit = max(1, min(limit, 2000))

    filters: dict[str, object] = {}
    meeting_key = _coerce_int_or_none(request.GET.get("meeting_key"))
    session_key = _coerce_int_or_none(request.GET.get("session_key"))
    driver_number = _coerce_int_or_none(request.GET.get("driver_number"))

    if meeting_key is not None:
        filters["meeting_key"] = meeting_key
    if session_key is not None:
        filters["session_key"] = session_key
    if driver_number is not None:
        filters["driver_number"] = driver_number

    is_manual = request.GET.get("is_manual")
    if isinstance(is_manual, str) and is_manual.lower() in {"1", "true", "yes"}:
        filters["is_manual"] = True
    elif isinstance(is_manual, str) and is_manual.lower() in {"0", "false", "no"}:
        filters["is_manual"] = False

    queryset = Car.objects.all()
    if filters:
        queryset = queryset.filter(**filters)

    car_list = list(queryset.order_by("-date")[:limit])
    _attach_session_metadata(car_list)
    data = [serialize_car(car) for car in car_list]
    return JsonResponse(data, safe=False)


@login_required(login_url="/login")
def show_xml_by_id(request, car_id):
    car_item = Car.objects.filter(pk=car_id)
    if not car_item.exists():
        return HttpResponse(status=404)

    xml_data = serializers.serialize("xml", car_item)
    return HttpResponse(xml_data, content_type="application/xml")


@login_required(login_url="/login")
def show_json_by_id(request, car_id):
    car = get_object_or_404(Car, pk=car_id)
    return JsonResponse(serialize_car(car))

def all_cars_dashboard(request):
    return render(request, "all_cars.html")
# apps/car/views.py

from urllib.request import urlopen
from urllib.error import HTTPError, URLError

OPENF1_CAR_DATA_URL = "https://api.openf1.org/v1/car_data"

def _fetch_openf1_triplet(driver_number: int, session_key: int, min_speed: int | None = None) -> list[dict]:
    # Bangun URL manual supaya '>' tidak di-encode (hindari params urlencode)
    url = f"{OPENF1_CAR_DATA_URL}?driver_number={driver_number}&session_key={session_key}"
    if min_speed is not None:
        url += f"&speed>={int(min_speed)}"  # '>' tetap '>' (bukan %3E)

    try:
        with urlopen(url, timeout=15) as resp:
            payload = resp.read()
    except HTTPError as exc:
        if exc.code == 422:
            return []
        raise
    except URLError:
        return []

    # parsing "best effort" seperti util yang sudah ada
    try:
        data = json.loads(payload)
        if not isinstance(data, list):
            return []
    except json.JSONDecodeError:
        data = _loads_json_array_best_effort(payload)

    return data if isinstance(data, list) else []


def _serialize_car_sample_for_group(sample: Car) -> dict:
    date_value = sample.date
    return {
        "id": str(sample.id),
        "date": date_value.isoformat() if date_value else None,
        "timestamp": localtime(date_value).strftime("%Y-%m-%d %H:%M:%S %Z") if date_value else None,
        "speed": sample.speed,
        "rpm": sample.rpm,
        "throttle": sample.throttle,
        "brake": sample.brake,
        "gear": sample.n_gear,
        "drs": sample.drs,
    }


def _build_groups_from_samples(samples: List[Car]) -> List[Dict]:
    groups: List[Dict] = []
    current_key: tuple | None = None
    current_group: Dict | None = None

    for sample in samples:
        key = (sample.driver_number, sample.session_key, sample.meeting_key)
        if current_group is None or key != current_key:
            current_key = key
            current_group = {
                "session_key": sample.session_key,
                "meeting_key": sample.meeting_key,
                "driver_number": sample.driver_number,
                "telemetry": [],
            }
            groups.append(current_group)

        current_group["telemetry"].append(_serialize_car_sample_for_group(sample))

    return groups


@require_GET
def api_grouped_car_data(request):
    metric = request.GET.get("metric", "speed")
    allowed_metrics = {"speed", "rpm", "throttle"}
    if metric not in allowed_metrics:
        metric = "speed"

    driver_number = request.GET.get("driver_number")
    session_key = request.GET.get("session_key")
    meeting_key = request.GET.get("meeting_key")
    min_speed = request.GET.get("min_speed") 

    try:
        driver_number_int = int(driver_number) if driver_number is not None else None
        session_key_int = int(session_key) if session_key is not None else None
        meeting_key_int = int(meeting_key) if meeting_key is not None else None
        min_speed_int = int(min_speed) if min_speed is not None else None
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Invalid query params."}, status=400)

    has_driver_session = (
        driver_number_int is not None and session_key_int is not None
    )

    if meeting_key_int is None and not has_driver_session:
        return JsonResponse(
            {
                "ok": False,
                "error": "meeting_key or (driver_number + session_key) are required.",
            },
            status=400,
        )

    filters: Dict[str, int] = {}
    if meeting_key_int is not None:
        filters["meeting_key"] = meeting_key_int
    if session_key_int is not None:
        filters["session_key"] = session_key_int
    if driver_number_int is not None:
        filters["driver_number"] = driver_number_int

    queryset = (
        Car.objects.filter(**filters)
        .order_by("driver_number", "session_key", "date")
    )

    samples_db = list(queryset)

    if samples_db:
        groups_payload = _build_groups_from_samples(samples_db)
    elif has_driver_session:
        raw = _fetch_openf1_triplet(
            driver_number=driver_number_int,
            session_key=session_key_int,
            min_speed=min_speed_int,  
        )

        telemetry_rows = [
            {
                "id": None,
                "date": r.get("date"),
                "timestamp": r.get("date"),  
                "speed": r.get("speed"),
                "rpm": r.get("rpm"),
                "throttle": r.get("throttle"),
                "brake": r.get("brake"),
                "gear": r.get("n_gear"),
                "drs": r.get("drs"),
            }
            for r in raw
            if r.get("session_key") == session_key_int and r.get("driver_number") == driver_number_int
        ]

        mk = meeting_key_int
        if raw:
            try:
                mk = int(raw[0].get("meeting_key"))
            except (TypeError, ValueError):
                mk = meeting_key_int

        groups_payload = [{
            "session_key": session_key_int,
            "meeting_key": mk,
            "driver_number": driver_number_int,
            "telemetry": telemetry_rows,
        }]
    else:
        groups_payload = []

    return JsonResponse(
        {
            "ok": True,
            "metric": metric,
            "metric_options": sorted(list(allowed_metrics)),
            "groups": groups_payload,
        }
    )



OPENF1_CAR_DATA_URL = "https://api.openf1.org/v1/car_data"
OPENF1_MIN_SPEED_FLOOR = 310


def _fetch_meeting_choices(extra_keys: Sequence[int] | None = None) -> list[tuple[int, str]]:
    choices: list[tuple[int, str]] = []
    seen: set[int] = set()

    meetings = Meeting.objects.all().order_by("-date_start", "-meeting_key")
    for meeting in meetings:
        key = meeting.meeting_key
        if key is None or key in seen:
            continue
        label = meeting.meeting_name or meeting.circuit_short_name or meeting.country_name or str(key)
        if meeting.year:
            label = f"{label} ({meeting.year})"
        choices.append((key, f"{key} - {label}"))
        seen.add(key)

    if extra_keys:
        for key in extra_keys:
            if key is None:
                continue
            try:
                key_int = int(key)
            except (TypeError, ValueError):
                continue
            if key_int in seen:
                continue
            choices.append((key_int, str(key_int)))
            seen.add(key_int)

    choices.sort(key=lambda item: item[0])
    return choices


def _fetch_openf1_telemetry(meeting_key: int, min_speed: int) -> List[Dict]:
    url = f"{OPENF1_CAR_DATA_URL}?meeting_key={meeting_key}&speed>={min_speed}"
    try:
        with urlopen(url) as response:
            payload = response.read()
    except HTTPError as exc:
        if exc.code == 422:
            return []
        raise

    try:
        data = json.loads(payload)
        if not isinstance(data, list):
            return []
    except json.JSONDecodeError:
        data = _loads_json_array_best_effort(payload)

    if not isinstance(data, list):
        return []
    return data


@require_POST
def api_refresh_car_data(request):
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON payload."}, status=400)

    meeting_key = body.get("meeting_key")
    min_speed = body.get("min_speed", OPENF1_MIN_SPEED_FLOOR)
    max_speed = body.get("max_speed")

    try:
        meeting_key = int(meeting_key)
    except (TypeError, ValueError):
        return JsonResponse(
            {"ok": False, "error": "meeting_key must be an integer."},
            status=400,
        )

    try:
        min_speed = int(min_speed)
    except (TypeError, ValueError):
        min_speed = OPENF1_MIN_SPEED_FLOOR

    try:
        max_speed_int = int(max_speed) if max_speed is not None else None
    except (TypeError, ValueError):
        return JsonResponse(
            {"ok": False, "error": "max_speed must be an integer when provided."},
            status=400,
        )

    try:
        dataset = _fetch_openf1_telemetry(meeting_key, min_speed)
    except (HTTPError, URLError) as exc:
        return JsonResponse(
            {"ok": False, "error": f"Failed to retrieve telemetry: {exc}"},
            status=502,
        )

    dataset = [
        entry
        for entry in dataset
        if entry.get("speed") is not None
        and (max_speed_int is None or entry["speed"] <= max_speed_int)
    ]

    meeting_cache: set[int] = set()
    session_cache: dict[int, Session] = {}

    with transaction.atomic():
        deleted_count, _ = Car.objects.filter(
            is_manual=False, meeting_key=meeting_key
        ).delete()
        created = 0
        for entry in dataset:
            try:
                mk = int(entry["meeting_key"])
                sk = int(entry["session_key"])
            except (KeyError, TypeError, ValueError):
                continue

            if mk not in meeting_cache:
                Meeting.objects.get_or_create(meeting_key=mk)
                meeting_cache.add(mk)

            session_obj = session_cache.get(sk)
            if session_obj is None:
                session_obj, _ = Session.objects.get_or_create(
                    session_key=sk,
                    defaults={"meeting_key": mk},
                )
            elif session_obj.meeting_key != mk:
                session_obj.meeting_key = mk
                session_obj.save(update_fields=["meeting_key"])
            session_cache[sk] = session_obj

            driver_number = entry.get("driver_number")
            try:
                driver_number = int(driver_number) if driver_number is not None else None
            except (TypeError, ValueError):
                driver_number = None

            if driver_number is None:
                continue

            Car.objects.create(
                driver_number=driver_number,
                session_key=sk,
                meeting_key=mk,
                date=parse_datetime(entry.get("date")),
                brake=entry.get("brake", 0),
                drs=entry.get("drs", 0),
                n_gear=entry.get("n_gear", 0),
                rpm=entry.get("rpm", 0),
                speed=entry.get("speed", 0),
                throttle=entry.get("throttle", 0),
                is_manual=False,
            )
            created += 1

    return JsonResponse(
        {
            "ok": True,
            "meeting_key": meeting_key,
            "min_speed": min_speed,
            "max_speed": max_speed_int,
            "created": created,
            "deleted": deleted_count,
        }
    )

@admin_required
def edit_car(request, id):
    car = get_object_or_404(Car, pk=id)

    extra_keys: list[int] = []
    if car.meeting_key is not None:
        extra_keys.append(car.meeting_key)
    if car.session_key is not None:
        session_obj = Session.objects.filter(session_key=car.session_key).first()
        if session_obj and session_obj.meeting_key is not None:
            extra_keys.append(session_obj.meeting_key)
    meeting_choices = _fetch_meeting_choices(extra_keys=extra_keys)
    meeting_keys = [choice[0] for choice in meeting_choices]
    form = CarForm(request.POST or None, instance=car, meeting_choices=meeting_choices)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        if form.is_valid():
            updated_car = form.save()
            payload = {
                "success": True,
                "message": "Car telemetry updated.",
                "car": serialize_car(updated_car),
            }
            if is_ajax:
                return JsonResponse(payload)

            messages.success(request, "Car telemetry updated.")
            return redirect("car:manual_list")

        if is_ajax:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

        messages.error(request, "Please correct the errors below.")

    session_catalog = _build_session_catalog(meeting_keys)

    return render(
        request,
        "edit_car.html",
        {
            "form": form,
            "car": car,
            "session_catalog": session_catalog,
        },
    )


@admin_required
def delete_car(request, id):
    car = get_object_or_404(Car, pk=id)

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        car.delete()
        if is_ajax:
            return JsonResponse({"success": True, "deleted_id": id})

        messages.success(request, "Car telemetry deleted.")
        return HttpResponseRedirect(reverse("car:manual_list"))

    if is_ajax:
        return JsonResponse(
            {"success": False, "message": "Unsupported method."}, status=405
        )

    session_obj = None
    if car.session_key is not None:
        session_obj = Session.objects.filter(session_key=car.session_key).first()

    return render(
        request,
        "car_confirm_delete.html",
        {
            "car": car,
            "session": session_obj,
        },
    )


@admin_required
def manual_list(request):
    manual_entries_qs = Car.objects.filter(is_manual=True).order_by("-date")
    manual_entries = list(manual_entries_qs)
    _attach_session_metadata(manual_entries)
    for car in manual_entries:
        car.display_date = localtime(car.date)

    return render(
        request,
        "manual_list.html",
        {
            "manual_entries": manual_entries,
        },
    )


def _attach_session_metadata(cars: list[Car]) -> None:
    session_keys = {
        car.session_key
        for car in cars
        if getattr(car, "session_key", None) is not None
    }
    if not session_keys:
        return
    session_map = {
        session.session_key: session
        for session in Session.objects.filter(session_key__in=session_keys)
    }
    for car in cars:
        car.session_obj = session_map.get(car.session_key)


@login_required(login_url="/login")
def manual_json(request):
    try:
        limit = int(request.GET.get("limit", 200))
    except (TypeError, ValueError):
        limit = 200
    limit = max(1, min(limit, 500))

    manual_entries_qs = (
        Car.objects.filter(is_manual=True)
        .order_by("-date")
        [:limit]
    )
    manual_entries = list(manual_entries_qs)
    _attach_session_metadata(manual_entries)
    data = [serialize_car(car) for car in manual_entries]
    return JsonResponse(data, safe=False)


def serialize_car(car: Car) -> dict:
    session_obj = getattr(car, "session_obj", None)
    if session_obj is None and car.session_key is not None:
        session_obj = Session.objects.filter(session_key=car.session_key).first()

    return {
        "id": str(car.id),
        "brake": car.brake,
        "date": car.date.isoformat() if car.date else None,
        "driver_number": car.driver_number,
        "drs": car.drs,
        "drs_state": car.drs_state,
        "meeting_key": car.meeting_key,
        "n_gear": car.n_gear,
        "rpm": car.rpm,
        "session_key": car.session_key,
        "session_name": session_obj.name if session_obj else None,
        "session_offset_seconds": _compute_session_offset_seconds(car),
        "is_manual": car.is_manual,
        "speed": car.speed,
        "throttle": car.throttle,
        "created_at": car.created_at.isoformat() if car.created_at else None,
        "updated_at": car.updated_at.isoformat() if car.updated_at else None,
    }
