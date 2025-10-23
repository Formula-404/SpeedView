import datetime
import json
from collections import defaultdict
from functools import wraps
from typing import Dict, Iterable, List
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


@admin_required
def add_car(request):
    form = CarForm(request.POST or None)
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

    return render(request, "add_car.html", {"form": form})


@login_required(login_url="/login")
def show_car(request, id):
    car = get_object_or_404(Car, pk=id)
    return render(request, "car_detail.html", {"car": car})


@admin_required
@require_POST
@csrf_exempt
def add_car_entry_ajax(request):
    form = CarForm(request.POST)
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
    lookup_map = {
        "meeting_key": "meeting_key_id",
        "session_key": "session_key_id",
    }
    for key in ("driver_number", "meeting_key", "session_key"):
        value = request.GET.get(key)
        if not value:
            continue
        lookup = lookup_map.get(key, key)
        if lookup.endswith("_id"):
            try:
                value = int(value)
            except ValueError:
                continue
        filters[lookup] = value
    queryset = (
        Car.objects.filter(**filters)
        .order_by("session_key", "meeting_key", "driver_number", "date")
    )

    grouped = defaultdict(list)
    for car in queryset:
        grouped[(car.session_key_id, car.meeting_key_id, car.driver_number)].append(car)

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


OPENF1_CAR_DATA_URL = "https://api.openf1.org/v1/car_data"


def _fetch_openf1_telemetry(
    meeting_key: int,
    min_speed: int,
) -> List[Dict]:
    try:
        with urlopen(f"{OPENF1_CAR_DATA_URL}?meeting_key={meeting_key}&speed>={min_speed}") as response:
            payload = response.read()
    except HTTPError as exc:
        if exc.code == 422:
            return []
        raise

    data = json.loads(payload)
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
    min_speed = body.get("min_speed")
    max_speed = body.get("max_speed")

    try:
        meeting_key = int(meeting_key)
        min_speed = int(min_speed)
        max_speed = int(max_speed)
    except (TypeError, ValueError):
        return JsonResponse(
            {"ok": False, "error": "meeting_key, min_speed, and max_speed must be integers."},
            status=400,
        )

    if max_speed < min_speed:
        return JsonResponse(
            {"ok": False, "error": "min_speed must be less than or equal to max_speed."},
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
        if entry.get("speed") is not None and entry["speed"] <= max_speed
    ]

    meeting_cache: dict[int, Meeting] = {}
    session_cache: dict[int, Session] = {}

    with transaction.atomic():
        deleted_count, _ = Car.objects.filter(
            is_manual=False, meeting_key_id=meeting_key
        ).delete()
        created = 0
        for entry in dataset:
            mk = entry["meeting_key"]
            sk = entry["session_key"]

            meeting_obj = meeting_cache.get(mk)
            if meeting_obj is None:
                meeting_obj, _ = Meeting.objects.get_or_create(meeting_key=mk)
                meeting_cache[mk] = meeting_obj

            session_obj = session_cache.get(sk)
            if session_obj is None:
                session_obj, _ = Session.objects.get_or_create(
                    session_key=sk,
                    defaults={"meeting": meeting_obj},
                )
                if meeting_obj and session_obj.meeting_id is None:
                    session_obj.meeting = meeting_obj
                    session_obj.save(update_fields=["meeting"])
                session_cache[sk] = session_obj

            Car.objects.create(
                driver_number=entry["driver_number"],
                session_key=session_obj,
                meeting_key=meeting_obj,
                date=parse_datetime(entry["date"]),
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
            "max_speed": max_speed,
            "created": created,
            "deleted": deleted_count,
        }
    )

@admin_required
def edit_car(request, id):
    car = get_object_or_404(Car, pk=id)

    form = CarForm(request.POST or None, instance=car)
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

    return render(request, "edit_car.html", {"form": form, "car": car})


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

    return HttpResponseRedirect(reverse("car:manual_list"))


@admin_required
def manual_list(request):
    manual_entries = (
        Car.objects.filter(is_manual=True).select_related("meeting_key", "session_key")
        .order_by("-date")
    )
    return render(
        request,
        "manual_list.html",
        {
            "manual_entries": manual_entries,
        },
    )


def serialize_car(car: Car) -> dict:
    return {
        "id": str(car.id),
        "brake": car.brake,
        "date": car.date.isoformat() if car.date else None,
        "driver_number": car.driver_number,
        "drs": car.drs,
        "drs_state": car.drs_state,
        "meeting_key": car.meeting_key_id,
        "n_gear": car.n_gear,
        "rpm": car.rpm,
        "session_key": car.session_key_id,
        "session_name": car.session_key.name if car.session_key else None,
        "speed": car.speed,
        "throttle": car.throttle,
        "created_at": car.created_at.isoformat() if car.created_at else None,
        "updated_at": car.updated_at.isoformat() if car.updated_at else None,
    }
