import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect
from django.db import IntegrityError, transaction
from django.urls import reverse

from .models import Driver
from .forms import DriverForm
from django.views.decorators.http import require_http_methods


# ================== helpers ==================
def is_admin(request):
    if not request.user.is_authenticated:
        return False
    profile = getattr(request.user, "profile", None)
    return getattr(profile, "role", None) == "admin"

def serialize_driver(driver: Driver):
    return {
        "driver_number": driver.driver_number,
        "full_name": driver.full_name,
        "broadcast_name": driver.broadcast_name or "",
        "headshot_url": driver.headshot_url or "",
        # "team_name": driver.team_name or "",
        "country_code": driver.country_code or "",
        # "team_colour": driver.team_colour or "",
        # "session_key": driver.session_key or "",
        "created_at": driver.created_at.isoformat() if driver.created_at else None,
        "updated_at": driver.updated_at.isoformat() if driver.updated_at else None,
        "detail_url": driver.get_absolute_url(),
    }

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

# ================== Page ==================
def driver_list_page(request):
    drivers = Driver.objects.all()
    return render(request, "driver_list.html", {"drivers": drivers})

def driver_detail_page(request, driver_number):
    driver = get_object_or_404(Driver, pk=driver_number)
    return render(request, "driver_detail.html", {"driver": driver})

def add_driver_page(request):
    if not request.user.is_authenticated:
        return redirect('user:login')
    # if not is_admin(request):
    #     return redirect('driver:list_page')
    return render(request, "add_driver.html", {"form": DriverForm()})

def edit_driver_page(request, driver_number):
    if not request.user.is_authenticated:
        return redirect('user:login')
    # if not is_admin(request):
    #     return redirect('driver:driver_list')
    driver = get_object_or_404(Driver, pk=driver_number)
    return render(request, "edit_driver.html", {"form": DriverForm(instance=driver)})

@csrf_protect
@require_http_methods(["GET", "POST"])
def delete_driver_page(request, driver_number):
    if not request.user.is_authenticated or not is_admin(request):
        # non-admin diarahkan ke detail saja
        return redirect('driver:driver_detail', driver_number=driver_number)

    driver = get_object_or_404(Driver, pk=driver_number)

    if request.method == "POST":
        driver.delete()
        return redirect('driver:driver_list')

    return render(request, "driver_confirm_delete.html", {"driver": driver})

# ================== API ==================
@require_GET
def api_driver_list(request):
    drivers = Driver.objects.all()
    data = [serialize_driver(d) for d in drivers]
    return JsonResponse({"ok": True, "count": len(data), "data": data})

@require_GET
def api_driver_detail(request, driver_number):
    driver = get_object_or_404(Driver, pk=driver_number)
    return JsonResponse({"ok": True, "data": serialize_driver(driver)})

@csrf_protect
@require_POST
def api_driver_create(request):
    if not request.user.is_authenticated:
        return json_error("Authentication required.", status=401)
    # if not is_admin(request):
    #     return json_error("Admin role required.", status=403)

    payload = request.POST.dict() or parse_json(request)
    if payload is None:
        return HttpResponseBadRequest("Invalid JSON body.")
    form = DriverForm(payload)
    if form.is_valid():
        try:
            with transaction.atomic():
                driver = form.save()

            if request.headers.get("X-Requested-With") != "XMLHttpRequest" and \
               "application/json" not in request.headers.get("Accept", ""):
                return HttpResponseRedirect(reverse("driver:driver_list"))

            return JsonResponse({"ok": True, "data": serialize_driver(driver)}, status=201)

        except IntegrityError:
            form.add_error("driver_number", "A driver with this number already exists.")

    if request.headers.get("X-Requested-With") != "XMLHttpRequest" and \
       "application/json" not in request.headers.get("Accept", ""):
        return render(request, "add_driver.html", {"form": form})
    return json_error("Validation failed", field_errors=form.errors, status=422)

@csrf_protect
def api_driver_update(request, driver_number):
    if not request.user.is_authenticated:
        return json_error("Authentication required.", status=401)
    if not is_admin(request):
        return json_error("Admin role required.", status=403)

    driver = get_object_or_404(Driver, pk=driver_number)
    payload = parse_json(request) or request.POST.dict()
    if payload is None:
        return HttpResponseBadRequest("Invalid JSON body.")

    form = DriverForm(payload, instance=driver)
    if form.is_valid():
        try:
            with transaction.atomic():
                updated = form.save()
            return JsonResponse({"ok": True, "data": serialize_driver(updated)})
        except IntegrityError:
            form.add_error("driver_number", "Another driver already uses this number.")
    return json_error("Validation failed", field_errors=form.errors, status=422)

@csrf_protect
def api_driver_delete(request, driver_number):
    if not request.user.is_authenticated:
        return json_error("Authentication required.", status=401)
    # if not is_admin(request):
    #     return json_error("Admin role required.", status=403)

    driver = get_object_or_404(Driver, pk=driver_number)
    driver.delete()
    return JsonResponse({"ok": True, "deleted": driver_number})
