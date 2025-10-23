import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from .models import Comparison, ComparisonTeam
from apps.team.models import Team

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

# ================== pages ==================
@login_required
def create_page(request):
    return render(request, "comparison_create.html")

@login_required
def detail_page(request, pk):
    cmp = get_object_or_404(Comparison, pk=pk, owner=request.user)
    if cmp.module != Comparison.MODULE_TEAM:
        return render(request, "comparison_detail_generic.html", {"cmp": cmp})

    links = (ComparisonTeam.objects
             .select_related("team")
             .filter(comparison=cmp)
             .order_by("order_index"))
    teams = [l.team for l in links]
    return render(request, "comparison_team_detail.html", {"cmp": cmp, "teams": teams})



# ================== api ==================
@login_required
@require_POST
def api_comparison_create(request):
    data = parse_json(request) or request.POST.dict()
    if data is None:
        return HttpResponseBadRequest("Invalid JSON body.")

    module = data.get("module")
    items = data.get("items") or []
    if isinstance(items, str):
        items = [x.strip() for x in items.split(",") if x.strip()]

    if module not in dict(Comparison.MODULE_CHOICES):
        return json_error("Invalid module", status=422)
    if not (2 <= len(items) <= 4):
        return json_error("Select between 2 and 4 items.", status=422)

    cmp = Comparison.objects.create(owner=request.user, module=module)

    if module == Comparison.MODULE_TEAM:
        teams = Team.objects.filter(pk__in=items)
        if teams.count() != len(items):
            return json_error("One or more teams not found.", status=404)
        name_to_team = {t.pk: t for t in teams}
        for idx, pk in enumerate(items):
            ComparisonTeam.objects.create(comparison=cmp, team=name_to_team[pk], order_index=idx)
    else:
        return json_error("This module is not implemented yet.", status=422)

    return JsonResponse({"ok": True, "redirect": cmp.get_absolute_url()})

@login_required
@require_GET
def api_comparison_detail(request, pk):
    cmp = get_object_or_404(Comparison, pk=pk, owner=request.user)
    payload = {"id": str(cmp.pk), "module": cmp.module}
    if cmp.module == Comparison.MODULE_TEAM:
        links = (ComparisonTeam.objects
                 .select_related("team")
                 .filter(comparison=cmp)
                 .order_by("order_index"))
        payload: dict[str, object] = {"id": str(cmp.pk), "module": cmp.module}
        payload["items"] = [serialize_team_for_compare(l.team) for l in links]

        return JsonResponse({"ok": True, "data": payload})
    return json_error("Unsupported module.", status=422)

