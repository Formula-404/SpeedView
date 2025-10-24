import datetime
import json
from collections import defaultdict
from functools import wraps
from typing import Dict, Iterable, List, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import requests
from django.conf import settings
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
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from apps.car.forms import CarForm
from apps.car.models import Car
from apps.session.models import Session
from apps.session.services import ensure_sessions_for_meetings
from apps.meeting.models import Meeting


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if not (getattr(profile, "role", None) == "admin"):
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
                "value": str(session.session_key),
                "label": str(session),
            }
        )

    return catalog


@admin_required
def add_car(request):
    meeting_choices = _fetch_meeting_choices()
    meeting_keys = [choice[0] for choice in meeting_choices]
    ensure_sessions_for_meetings(meeting_keys)
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


@login_required(login_url="/login")
def show_car(request, id):
    car = get_object_or_404(Car, pk=id)
    return render(request, "car_detail.html", {"car": car})


@admin_required
@require_POST
@csrf_exempt
def add_car_entry_ajax(request):
    meeting_choices = _fetch_meeting_choices()
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


@login_required(login_url="/login")
def show_xml(request):
    car_list = Car.objects.all()
    xml_data = serializers.serialize("xml", car_list)
    return HttpResponse(xml_data, content_type="application/xml")


@login_required(login_url="/login")
def show_json(request):
    car_list = Car.objects.all()
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

@login_required(login_url="/login")
def all_cars_dashboard(request):
    return render(request, "all_cars.html")

@require_GET
@login_required(login_url="/login")
def api_grouped_car_data(request):
    metric = request.GET.get("metric", "speed")
    allowed_metrics = {"speed", "rpm", "throttle"}
    if metric not in allowed_metrics:
        metric = "speed"

    filters = {}
    for key in ("driver_number", "meeting_key", "session_key"):
        value = request.GET.get(key)
        if not value:
            continue
        try:
            filters[key] = int(value)
        except ValueError:
            continue
    queryset = (
        Car.objects.filter(**filters)
        .order_by("session_key", "meeting_key", "driver_number", "date")
    )

    grouped = defaultdict(list)
    for car in queryset:
        grouped[(car.session_key, car.meeting_key, car.driver_number)].append(car)

    groups_payload = []
    for (session_key, meeting_key, driver_number), samples in grouped.items():
        telemetry = [
            {
                "id": str(sample.id),
                "date": sample.date.isoformat() if sample.date else None,
                "timestamp": localtime(sample.date).strftime("%Y-%m-%d %H:%M:%S %Z")
                if sample.date
                else None,
                "speed": sample.speed,
                "rpm": sample.rpm,
                "throttle": sample.throttle,
                "brake": sample.brake,
                "gear": sample.n_gear,
                "drs": sample.drs,
            }
            for sample in samples
        ]
        groups_payload.append(
            {
                "session_key": session_key,
                "meeting_key": meeting_key,
                "driver_number": driver_number,
                "telemetry": telemetry,
            }
        )

    return JsonResponse(
        {
            "ok": True,
            "metric": metric,
            "metric_options": sorted(list(allowed_metrics)),
            "groups": groups_payload,
        }
    )


OPENF1_MEETINGS_URL = "https://api.openf1.org/v1/meetings"
OPENF1_CAR_DATA_URL = "https://api.openf1.org/v1/car_data"
OPENF1_MIN_SPEED_FLOOR = 310


def _fetch_meeting_choices(extra_keys: Sequence[int] | None = None) -> list[tuple[int, str]]:
    choices: list[tuple[int, str]] = []
    seen: set[int] = set()

    try:
        response = requests.get(OPENF1_MEETINGS_URL, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        payload = []

    if isinstance(payload, list):
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            key = entry.get("meeting_key")
            try:
                key_int = int(key)
            except (TypeError, ValueError):
                continue
            if key_int in seen:
                continue
            label = (
                entry.get("meeting_name")
                or entry.get("circuit_short_name")
                or entry.get("country_name")
                or str(key_int)
            )
            choices.append((key_int, f"{key_int} - {label}"))
            seen.add(key_int)

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


def _fetch_meeting_choices(extra_keys: Sequence[int] | None = None) -> list[tuple[int, str]]:
    choices: list[tuple[int, str]] = []
    seen: set[int] = set()

    try:
        response = requests.get(OPENF1_MEETINGS_URL, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        payload = []

    if isinstance(payload, list):
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            key = entry.get("meeting_key")
            try:
                key_int = int(key)
            except (TypeError, ValueError):
                continue
            if key_int in seen:
                continue
            label = (
                entry.get("meeting_name")
                or entry.get("circuit_short_name")
                or entry.get("country_name")
                or str(key_int)
            )
            choices.append((key_int, f"{key_int} - {label}"))
            seen.add(key_int)

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


def _fetch_openf1_telemetry(
    meeting_key: int,
    min_speed: int,
) -> List[Dict]:
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
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return data


@require_POST
@login_required(login_url="/login")
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
    ensure_sessions_for_meetings(meeting_keys)
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

    session_keys = {car.session_key for car in manual_entries if car.session_key is not None}
    session_map = {
        session.session_key: session
        for session in Session.objects.filter(session_key__in=session_keys)
    }
    for car in manual_entries:
        car.session_obj = session_map.get(car.session_key)
        display_date = car.date
        if display_date:
            if timezone.is_aware(display_date):
                display_date = timezone.make_naive(
                    display_date, datetime.timezone.utc
                )
            display_date = display_date + datetime.timedelta(hours=7)
        car.display_date = display_date

    return render(
        request,
        "manual_list.html",
        {
            "manual_entries": manual_entries,
        },
    )


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
        "speed": car.speed,
        "throttle": car.throttle,
        "created_at": car.created_at.isoformat() if car.created_at else None,
        "updated_at": car.updated_at.isoformat() if car.updated_at else None,
    }
