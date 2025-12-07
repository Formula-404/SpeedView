import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.db import transaction
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q, Prefetch
from .models import *
from apps.team.models import Team
from apps.circuit.models import Circuit
from apps.driver.models import Driver
from apps.car.models import Car

# ================== helpers ==================
def parse_json(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return None

def json_error(message, status=400, field_errors=None):
    payload = {"ok": False, "error": message}
    if field_errors:
        payload["field_errors"] = field_errors
    return JsonResponse(payload, status=status)

# ================== helpers ==================
def serialize_comparison(cmp: Comparison) -> dict:
    if cmp.module == Comparison.MODULE_TEAM:
        items = list(
            ComparisonTeam.objects.select_related("team")
            .filter(comparison=cmp).order_by("order_index")
            .values_list("team__team_name", flat=True)
        )

    elif cmp.module == Comparison.MODULE_CIRCUIT:
        items = list(
            ComparisonCircuit.objects.select_related("circuit")
            .filter(comparison=cmp).order_by("order_index")
            .values_list("circuit__name", flat=True)
        )

    elif cmp.module == Comparison.MODULE_DRIVER:
        # Use full name / broadcast name as label in list view
        items = list(
            ComparisonDriver.objects.select_related("driver")
            .filter(comparison=cmp).order_by("order_index")
            .values_list("driver__full_name", flat=True)
        )

    else:
        items = []

    owner_name = getattr(cmp.owner, "username", "") or (
        cmp.owner.get_username() if hasattr(cmp.owner, "get_username") else ""
    )

    return {
        "id": str(cmp.pk),
        "title": cmp.title,
        "module": cmp.module,
        "module_label": cmp.get_module_display(),  # type: ignore
        "is_public": cmp.is_public,
        "owner_name": owner_name or "—",
        "created_at": cmp.created_at.isoformat() if cmp.created_at else "",
        "detail_url": cmp.get_absolute_url(),
        "items": items,
    }


def serialize_team_for_compare(t: Team):
    return {
        "team_name": t.team_name,
        "short_code": t.short_code or "",
        "team_logo_url": t.team_logo_url,
        "team_colour_hex": f"#{t.team_colour}",
        "country": t.country or "",
        "base": t.base or "",
        "founded_year": t.founded_year,
        "engines": t.engines or "",
        "website": t.website or "",
        "wiki_url": t.wiki_url or "",
        "races_entered": t.races_entered,
        "race_victories": t.race_victories,
        "podiums": t.podiums,
        "points": t.points,
        "avg_lap_time_ms": t.avg_lap_time_ms,
        "best_lap_time_ms": t.best_lap_time_ms,
        "avg_pit_duration_ms": t.avg_pit_duration_ms,
        "top_speed_kph": t.top_speed_kph,
        "laps_completed": t.laps_completed,
        "detail_url": t.get_absolute_url(),
    }

def serialize_circuit_for_compare(c: Circuit) -> dict:
    label = getattr(c, "name", None) or str(c)
    return {
        "label": label,
        "country": getattr(c, "country", None),
        "length_km": getattr(c, "length_km", None),
        "detail_url": getattr(c, "get_absolute_url", lambda: "")(),
    }

def serialize_driver_for_compare(d: Driver):
    label = getattr(d, "full_name", None) or getattr(d, "name", None) or str(d)
    number = getattr(d, "number", None) or getattr(d, "driver_number", None)
    return {
        "label": label,
        "number": number if number is not None else "",
        "detail_url": getattr(d, "get_absolute_url", lambda: "")(),
    }

def serialize_car_for_compare(c: Car):
    label = getattr(c, "name", None) or f"Car #{getattr(c, 'driver_number', '—')}"
    return {
        "label": label,
        "driver_number": getattr(c, "driver_number", None),
        "meeting_key": getattr(c, "meeting_key", None),
        "session_key": getattr(c, "session_key", None),
        "detail_url": getattr(c, "get_absolute_url", lambda: "")(),
    }

def _auth_mobile_user(payload):
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return None, json_error("username and password are required.", status=401)

    user = authenticate(username=username, password=password)
    if user is None:
        return None, json_error("Invalid credentials.", status=401)

    return user, None


# ================== pages ==================
def list_page(request):
    return render(request, "comparison_list.html")

@login_required
def create_page(request):
    return render(request, "comparison_create.html")

@login_required
def detail_page(request, pk):
    cmp = get_object_or_404(Comparison, pk=pk)
    if cmp.owner != request.user and not cmp.is_public:
        return render(request, "comparison_list.html", status=403)


    if cmp.module == Comparison.MODULE_TEAM:
        links = (ComparisonTeam.objects.select_related("team")
            .filter(comparison=cmp).order_by("order_index"))
        teams = [l.team for l in links]
        return render(request, "comparison_team_detail.html", {"cmp": cmp, "teams": teams})


    if cmp.module == Comparison.MODULE_CIRCUIT:
        links = (ComparisonCircuit.objects.select_related("circuit")
            .filter(comparison=cmp).order_by("order_index"))
        circuits = [l.circuit for l in links]
        return render(request, "comparison_circuit_detail.html", {"cmp": cmp, "circuits": circuits})


    if cmp.module == Comparison.MODULE_DRIVER:
        links = (ComparisonDriver.objects.select_related("driver")
            .filter(comparison=cmp).order_by("order_index"))
        drivers = [l.driver for l in links]
        return render(request, "comparison_driver_detail.html", {"cmp": cmp, "drivers": drivers})


    if cmp.module == Comparison.MODULE_CAR:
        links = (ComparisonCar.objects.select_related("car")
            .filter(comparison=cmp).order_by("order_index"))
        cars = [l.car for l in links]
        return render(request, "comparison_car_detail.html", {"cmp": cmp, "cars": cars})


    return render(request, "comparison_detail_generic.html", {"cmp": cmp})


# ================== api ==================
@csrf_protect
@require_POST
def api_comparison_create(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    title = (payload.get("title") or "").strip() or "My Comparison"
    module = (payload.get("module") or "").strip()
    items = payload.get("items") or []
    is_public = bool(payload.get("is_public"))

    if module not in {Comparison.MODULE_TEAM, Comparison.MODULE_DRIVER, Comparison.MODULE_CIRCUIT}:
        return JsonResponse({"ok": False, "error": "Unknown module."}, status=400)
    if not (2 <= len(items) <= 4):
        return JsonResponse({"ok": False, "error": "Pick 2–4 items."}, status=400)

    with transaction.atomic():
        cmp = Comparison.objects.create(
            owner=request.user,
            module=module,
            title=title,
            is_public=is_public,
        )

    if module == Comparison.MODULE_TEAM:
        for idx, team_pk in enumerate(items):
            team = get_object_or_404(Team, pk=team_pk)
            ComparisonTeam.objects.create(comparison=cmp, team=team, order_index=idx)
    elif module == Comparison.MODULE_CIRCUIT:
        for idx, raw_pk in enumerate(items):
            pk = int(raw_pk)
            circuit = get_object_or_404(Circuit, pk=pk)
            ComparisonCircuit.objects.create(comparison=cmp, circuit=circuit, order_index=idx)
    elif module == Comparison.MODULE_DRIVER:
        for idx, raw_pk in enumerate(items):
            pk = int(raw_pk)
            driver = get_object_or_404(Driver, pk=pk)
            ComparisonDriver.objects.create(comparison=cmp, driver=driver, order_index=idx)

    return JsonResponse({"ok": True, "redirect": cmp.get_absolute_url()})

@require_GET
def api_comparison_list(request):
    scope = request.GET.get("scope", "all")
    qs = Comparison.objects.select_related("owner").order_by("-created_at")

    if scope == "my":
        qs = qs.filter(owner=request.user) if request.user.is_authenticated else Comparison.objects.none()
    else:
        if request.user.is_authenticated:
            qs = qs.filter(Q(is_public=True) | Q(owner=request.user))
        else:
            qs = qs.filter(is_public=True)

    data = [serialize_comparison(c) for c in qs]
    return JsonResponse({"ok": True, "count": len(data), "data": data})


@require_GET
def api_comparison_detail(request, pk):
    cmp = get_object_or_404(Comparison, pk=pk)
    payload: dict[str, object] = {"id": str(cmp.pk), "module": cmp.module}


    if cmp.module == Comparison.MODULE_TEAM:
        links = (ComparisonTeam.objects.select_related("team")
            .filter(comparison=cmp).order_by("order_index"))
        payload["items"] = [serialize_team_for_compare(l.team) for l in links]
        return JsonResponse({"ok": True, "data": payload})

    if cmp.module == Comparison.MODULE_CIRCUIT:
        links = (ComparisonCircuit.objects.select_related("circuit")
                 .filter(comparison=cmp).order_by("order_index"))
        payload["items"] = [serialize_circuit_for_compare(l.circuit) for l in links]
        return JsonResponse({"ok": True, "data": payload})

    if cmp.module == Comparison.MODULE_DRIVER:
        links = (ComparisonDriver.objects.select_related("driver")
            .filter(comparison=cmp).order_by("order_index"))
        payload["items"] = [serialize_driver_for_compare(l.driver) for l in links]
        return JsonResponse({"ok": True, "data": payload})

    if cmp.module == Comparison.MODULE_CAR:
        links = (ComparisonCar.objects.select_related("car")
            .filter(comparison=cmp).order_by("order_index"))
        payload["items"] = [serialize_car_for_compare(l.car) for l in links]
        return JsonResponse({"ok": True, "data": payload})


    return json_error("Unsupported module.", status=422)

@csrf_protect
@require_POST
def api_comparison_delete(request, pk):
    cmp = get_object_or_404(Comparison, pk=pk)
    is_admin = getattr(getattr(request.user, "profile", None), "role", None) == "admin"
    if cmp.owner != request.user and not is_admin:
        return HttpResponseForbidden("Not allowed")
    cmp.delete()
    return JsonResponse({"ok": True, "redirect": reverse("comparison:list_page")})

# ================== mobile API ==================
@require_GET
def api_mobile_comparison_list(request):
    scope = request.GET.get("scope", "all")
    owner_username = request.GET.get("owner", "").strip()

    qs = Comparison.objects.select_related("owner").order_by("-created_at")

    if scope == "all":
        qs = qs.filter(is_public=True)

    elif scope == "my":
        if not owner_username:
            qs = qs.filter(is_public=True)
        else:
            qs = qs.filter(owner__username=owner_username)

    else:
        return JsonResponse({"ok": False, "error": "Invalid scope"}, status=400)

    data = [serialize_comparison(c) for c in qs]
    return JsonResponse({"ok": True, "count": len(data), "data": data})

@csrf_exempt
@require_POST
def api_mobile_comparison_create(request):
    payload = parse_json(request)
    if payload is None:
        return json_error("Invalid JSON body.", status=400)

    user, err = _auth_mobile_user(payload)
    if err is not None:
        return err

    title = (payload.get("title") or "").strip() or "My Comparison"
    module = (payload.get("module") or "").strip()
    items = payload.get("items") or []
    is_public = bool(payload.get("is_public"))

    if module not in {
        Comparison.MODULE_TEAM,
        Comparison.MODULE_CAR,
        Comparison.MODULE_DRIVER,
        Comparison.MODULE_CIRCUIT,
    }:
        return json_error("Unknown module.", status=400)

    if not (2 <= len(items) <= 4):
        return json_error("Pick 2–4 items.", status=400)

    with transaction.atomic():
        cmp = Comparison.objects.create(
            owner=user,
            module=module,
            title=title,
            is_public=is_public,
        )

        if module == Comparison.MODULE_TEAM:
            for idx, team_pk in enumerate(items):
                team = get_object_or_404(Team, pk=team_pk)
                ComparisonTeam.objects.create(
                    comparison=cmp, team=team, order_index=idx
                )
        elif module == Comparison.MODULE_CIRCUIT:
            for idx, raw_pk in enumerate(items):
                pk = int(raw_pk)
                circuit = get_object_or_404(Circuit, pk=pk)
                ComparisonCircuit.objects.create(
                    comparison=cmp, circuit=circuit, order_index=idx
                )
        elif module == Comparison.MODULE_DRIVER:
            for idx, raw_pk in enumerate(items):
                pk = int(raw_pk)
                driver = get_object_or_404(Driver, pk=pk)
                ComparisonDriver.objects.create(
                    comparison=cmp, driver=driver, order_index=idx
                )
        elif module == Comparison.MODULE_CAR:
            for idx, raw_pk in enumerate(items):
                pk = int(raw_pk)
                car = get_object_or_404(Car, pk=pk)
                ComparisonCar.objects.create(
                    comparison=cmp, car=car, order_index=idx
                )

    return JsonResponse(
        {
            "ok": True,
            "data": {
                "id": str(cmp.pk),
                "detail_url": cmp.get_absolute_url(),
            },
        }
    )

@csrf_exempt
@require_POST
def api_mobile_comparison_update(request, pk):
    payload = parse_json(request)
    if payload is None:
        return json_error("Invalid JSON body.", status=400)

    user, err = _auth_mobile_user(payload)
    if err is not None:
        return err

    cmp = get_object_or_404(Comparison, pk=pk)

    if cmp.owner != user:
        return json_error("Not allowed to edit this comparison.", status=403)

    title = payload.get("title")
    is_public = payload.get("is_public")

    changed = False
    if isinstance(title, str):
        new_title = title.strip()
        if new_title:
            cmp.title = new_title
            changed = True

    if isinstance(is_public, bool):
        cmp.is_public = is_public
        changed = True

    if changed:
        cmp.save(update_fields=["title", "is_public"])

    return JsonResponse(
        {
            "ok": True,
            "data": {
                "id": str(cmp.pk),
                "title": cmp.title,
                "is_public": cmp.is_public,
            },
        }
    )

@csrf_exempt
@require_POST
def api_mobile_comparison_delete(request, pk):
    payload = parse_json(request)
    if payload is None:
        return json_error("Invalid JSON body.", status=400)

    user, err = _auth_mobile_user(payload)
    if err is not None:
        return err

    cmp = get_object_or_404(Comparison, pk=pk)

    is_admin = getattr(getattr(user, "profile", None), "role", None) == "admin"
    if cmp.owner != user and not is_admin:
        return json_error("Not allowed to delete this comparison.", status=403)

    cmp.delete()
    return JsonResponse({"ok": True})
