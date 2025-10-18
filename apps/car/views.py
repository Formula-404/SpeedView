import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from car.forms import CarForm
from car.models import Car


def admin_required(view_func):

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "message": "Admin access required."}, status=403
                )
            raise PermissionDenied("Admin access required.")
        return view_func(request, *args, **kwargs)

    return login_required(_wrapped, login_url="/login")


@login_required(login_url="/login")
def show_main(request):
    driver_number = request.GET.get("driver_number")
    session_key = request.GET.get("session_key")
    meeting_key = request.GET.get("meeting_key")

    car_list = Car.objects.order_by("-date")
    if driver_number:
        car_list = car_list.filter(driver_number=driver_number)
    if session_key:
        car_list = car_list.filter(session_key=session_key)
    if meeting_key:
        car_list = car_list.filter(meeting_key=meeting_key)

    context = {
        "app": "SpeedView",
        "car_list": car_list,
        "last_login": request.COOKIES.get("last_login", "Never"),
        "filters": {
            "driver_number": driver_number or "",
            "meeting_key": meeting_key or "",
            "session_key": session_key or "",
        },
        "is_admin": request.user.is_staff or request.user.is_superuser,
    }
    return render(request, "main.html", context)


@admin_required
def add_car(request):
    form = CarForm(request.POST or None)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        if form.is_valid():
            car_entry = form.save()

            payload = {
                "success": True,
                "message": "Car telemetry entry created successfully.",
                "car": serialize_car(car_entry),
            }
            if is_ajax:
                return JsonResponse(payload, status=201)

            messages.success(request, payload["message"])
            return redirect("car:show_main")

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
                "message": "Car telemetry entry updated successfully.",
                "car": serialize_car(updated_car),
            }
            if is_ajax:
                return JsonResponse(payload)

            messages.success(request, payload["message"])
            return redirect("car:show_main")

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

        messages.success(request, "Car telemetry entry deleted successfully.")
        return HttpResponseRedirect(reverse("car:show_main"))

    if is_ajax:
        return JsonResponse(
            {"success": False, "message": "Unsupported method."}, status=405
        )

    return HttpResponseRedirect(reverse("car:show_main"))

def serialize_car(car: Car) -> dict:
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
        "speed": car.speed,
        "throttle": car.throttle,
        "created_at": car.created_at.isoformat() if car.created_at else None,
        "updated_at": car.updated_at.isoformat() if car.updated_at else None,
    }
