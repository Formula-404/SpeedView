from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Pit

# ================== Helpers ==================
def serialize_pit(pit: Pit):
    return {
        "pit_duration": pit.pit_duration,
        "date": pit.date.isoformat() if pit.date else None,
        "lap_number": pit.lap_number,
        "driver_number": pit.driver.driver_number,
        "session_key": pit.session.session_key,
        "meeting_key": pit.meeting.meeting_key,
        "created_at": pit.created_at.isoformat() if pit.created_at else None,
        "updated_at": pit.updated_at.isoformat() if pit.updated_at else None,
    }

# ================== Views ==================
def pit_list_page(request):
    pits = Pit.objects.all()
    return render(request, "pit_list.html", {"pits": pits})

def pit_detail_page(request, pit_id):
    pit = get_object_or_404(Pit, pk=pit_id)
    return render(request, "pit_detail.html", {"pit": pit})

# ================== API ==================
def api_pit_list(request):
    pits = Pit.objects.all()
    data = [serialize_pit(p) for p in pits]
    return JsonResponse({"ok": True, "count": len(data), "data": data})

def api_pit_detail(request, pit_id):
    pit = get_object_or_404(Pit, pk=pit_id)
    return JsonResponse({"ok": True, "data": serialize_pit(pit)})
