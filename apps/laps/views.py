from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Laps

# ================== Helpers ==================
def serialize_lap(lap: Laps):
    return {
        "lap_number": lap.lap_number,
        "driver_number": lap.driver.driver_number,
        "session_key": lap.session.session_key,
        "lap_duration": lap.lap_duration,
        "i1_speed": lap.i1_speed,
        "i2_speed": lap.i2_speed,
        "is_pit_out_lap": lap.is_pit_out_lap,
        "date_start": lap.date_start.isoformat() if lap.date_start else None,
        "created_at": lap.created_at.isoformat() if lap.created_at else None,
        "updated_at": lap.updated_at.isoformat() if lap.updated_at else None,
    }

# ================== Views ==================
def laps_list_page(request):
    laps = Laps.objects.all()
    return render(request, "laps_list.html", {"laps": laps})

def lap_detail_page(request, lap_number):
    lap = get_object_or_404(Laps, pk=lap_number)
    return render(request, "lap_detail.html", {"lap": lap})

# ================== API ==================
def api_laps_list(request):
    laps = Laps.objects.all()
    data = [serialize_lap(l) for l in laps]
    return JsonResponse({"ok": True, "count": len(data), "data": data})

def api_lap_detail(request, lap_number):
    lap = get_object_or_404(Laps, pk=lap_number)
    return JsonResponse({"ok": True, "data": serialize_lap(lap)})
