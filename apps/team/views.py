import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.contrib.auth import authenticate

from .models import Team
from .forms import TeamForm

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

def is_admin(user):
    if not user or not user.is_authenticated:
        return False
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None) == "admin"

def _auth_mobile_user(payload):
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return None, json_error("username and password are required.", status=401)

    user = authenticate(username=username, password=password)
    if user is None:
        return None, json_error("Invalid credentials.", status=401)

    return user, None

def serialize_team(team: Team):
    return {
        "team_name": team.team_name,
        "short_code": team.short_code or "",
        "team_logo_url": team.team_logo_url,
        "website": team.website or "",
        "wiki_url": team.wiki_url or "",

        "team_colour": team.team_colour,
        "team_colour_hex": f"#{team.team_colour}",
        "team_colour_secondary": team.team_colour_secondary or "",
        "team_colour_secondary_hex": f"#{team.team_colour_secondary}" if team.team_colour_secondary else "",

        "country": team.country or "",
        "base": team.base or "",
        "founded_year": team.founded_year,
        "is_active": team.is_active,

        "team_description": team.team_description or "",
        "engines": team.engines or "",

        "constructors_championships": team.constructors_championships,
        "drivers_championships": team.drivers_championships,
        "races_entered": team.races_entered,
        "race_victories": team.race_victories,
        "podiums": team.podiums,
        "points": team.points,

        "avg_lap_time_ms": team.avg_lap_time_ms,
        "best_lap_time_ms": team.best_lap_time_ms,
        "avg_pit_duration_ms": team.avg_pit_duration_ms,
        "top_speed_kph": team.top_speed_kph,
        "laps_completed": team.laps_completed,

        "created_at": team.created_at.isoformat() if team.created_at else None,
        "updated_at": team.updated_at.isoformat() if team.updated_at else None,

        "detail_url": team.get_absolute_url(),
    }

# ================== Page ==================
def team_list_page(request):
    return render(request, "team_list.html")

def team_detail_page(request, team_name):
    get_object_or_404(Team, pk=team_name)
    return render(request, "team_detail.html")

def add_team_page(request):
    if not request.user.is_authenticated:
        return redirect('user:login')
    if not is_admin(request):
        return redirect('team:list_page')
    return render(request, "add_team.html", {"form": TeamForm()})

def edit_team_page(request, team_name):
    if not request.user.is_authenticated:
        return redirect('user:login')
    if not is_admin(request):
        return redirect('team:list_page')
    team = get_object_or_404(Team, pk=team_name)
    if request.method == "POST":
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            updated = form.save()
            return redirect(updated.get_absolute_url())
        return render(request, "edit_team.html", {"form": form, "team": team})

    form = TeamForm(instance=team)
    return render(request, "edit_team.html", {"form": form, "team": team})


# ================== API ==================
@require_GET
def api_team_list(request):
    teams = Team.objects.all()
    data = [serialize_team(t) for t in teams]
    return JsonResponse({"ok": True, "count": len(data), "data": data})

@require_GET
def api_team_detail(request, team_name):
    team = get_object_or_404(Team, pk=team_name)
    return JsonResponse({"ok": True, "data": serialize_team(team)})

@csrf_protect
@require_POST
def api_team_create(request):
    if not request.user.is_authenticated:
        return json_error("Authentication required.", status=401)
    if not is_admin(request):
        return json_error("Admin role required.", status=403)

    payload = request.POST.dict() or parse_json(request)
    if payload is None:
        return HttpResponseBadRequest("Invalid JSON body.")
    form = TeamForm(payload)
    if form.is_valid():
        try:
            with transaction.atomic():
                team = form.save()

            if request.headers.get("X-Requested-With") != "XMLHttpRequest" and \
               "application/json" not in request.headers.get("Accept", ""):
                return HttpResponseRedirect(reverse("team:list_page"))

            return JsonResponse({"ok": True, "data": serialize_team(team)}, status=201)

        except IntegrityError:
            form.add_error("team_name", "A team with this name already exists.")

    if request.headers.get("X-Requested-With") != "XMLHttpRequest" and \
       "application/json" not in request.headers.get("Accept", ""):
        return render(request, "add_team.html", {"form": form})
    return json_error("Validation failed", field_errors=form.errors, status=422)

@csrf_protect
def api_team_update(request, team_name):
    if not request.user.is_authenticated:
        return json_error("Authentication required.", status=401)
    if not is_admin(request):
        return json_error("Admin role required.", status=403)

    team = get_object_or_404(Team, pk=team_name)
    payload = parse_json(request) or request.POST.dict()
    if payload is None:
        return HttpResponseBadRequest("Invalid JSON body.")

    form = TeamForm(payload, instance=team)
    if form.is_valid():
        try:
            with transaction.atomic():
                updated = form.save()
            return JsonResponse({"ok": True, "data": serialize_team(updated)})
        except IntegrityError:
            form.add_error("team_name", "Another team already uses this name.")
    return json_error("Validation failed", field_errors=form.errors, status=422)

@csrf_protect
def api_team_delete(request, team_name):
    if not request.user.is_authenticated:
        return json_error("Authentication required.", status=401)
    if not is_admin(request):
        return json_error("Admin role required.", status=403)

    team = get_object_or_404(Team, pk=team_name)
    team.delete()
    return JsonResponse({"ok": True, "deleted": team_name})

# ================== Mobile API ==================

@require_GET
def api_mobile_team_list(request):
    teams = Team.objects.all().order_by('team_name')
    data = [serialize_team(t) for t in teams]
    return JsonResponse({"ok": True, "count": len(data), "data": data})


@csrf_exempt
@require_POST
def api_mobile_team_create(request):
    payload = parse_json(request)
    if payload is None:
        return json_error("Invalid JSON body.", status=400)

    if request.user.is_authenticated:
        user = request.user
    else:
        user, err = _auth_mobile_user(payload)
        if err is not None:
            return err

    if not is_admin(user):
        return json_error("Admin role required.", status=403)

    form = TeamForm(payload)
    if form.is_valid():
        try:
            with transaction.atomic():
                team = form.save()
            return JsonResponse({
                "ok": True, 
                "data": serialize_team(team)
            }, status=201)
        except IntegrityError:
            return json_error("A team with this name already exists.", status=409)
    
    return json_error("Validation failed", field_errors=form.errors, status=422)


@csrf_exempt
@require_POST
def api_mobile_team_update(request, team_name):
    team = get_object_or_404(Team, pk=team_name)
    
    payload = parse_json(request)
    if payload is None:
        return json_error("Invalid JSON body.", status=400)

    if request.user.is_authenticated:
        user = request.user
    else:
        user, err = _auth_mobile_user(payload)
        if err is not None:
            return err

    if not is_admin(user):
        return json_error("Admin role required.", status=403)

    form = TeamForm(payload, instance=team)
    if form.is_valid():
        try:
            with transaction.atomic():
                updated = form.save()
            return JsonResponse({"ok": True, "data": serialize_team(updated)})
        except IntegrityError:
             return json_error("Another team already uses this name.", status=409)

    return json_error("Validation failed", field_errors=form.errors, status=422)


@csrf_exempt
@require_POST
def api_mobile_team_delete(request, team_name):
    team = get_object_or_404(Team, pk=team_name)
    
    payload = parse_json(request)
    if payload is None:
        return json_error("Invalid JSON body.", status=400)

    if request.user.is_authenticated:
        user = request.user
    else:
        user, err = _auth_mobile_user(payload)
        if err is not None:
            return err

    if not is_admin(user):
        return json_error("Admin role required.", status=403)

    team.delete()
    return JsonResponse({"ok": True, "deleted": team_name})