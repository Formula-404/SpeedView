import json
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.urls import reverse
from .models import Circuit
from .forms import CircuitForm
import traceback

# ================== Helpers ==================
def is_admin(request):
    """Mengecek apakah user terautentikasi dan punya role 'admin'."""
    if not request.user.is_authenticated:
        return False    
    profile = getattr(request.user, "profile", None)
    if profile:
        user_role = getattr(profile, "role", None)
        is_admin_user = (user_role == "admin") 
        return is_admin_user
    else:
        return False


def serialize_circuit(circuit: Circuit, request):
    """Mengubah objek Circuit menjadi dictionary yang aman untuk JSON."""
    return {
        "id": circuit.pk,
        "name": circuit.name or "", 
        "country": circuit.country or "",
        "location": circuit.location or "",
        "map_image_url": circuit.map_image_url or "",
        "circuit_type": circuit.circuit_type,
        "direction": circuit.direction,
        "length_km": circuit.length_km,
        "turns": circuit.turns,
        "grands_prix": circuit.grands_prix,
        "seasons": circuit.seasons,
        "grands_prix_held": circuit.grands_prix_held,
        'detail_url': reverse('circuit:detail_page', kwargs={'pk': circuit.pk}),
        'edit_url': reverse('circuit:edit_page', kwargs={'pk': circuit.pk}),
        'delete_url': reverse('circuit:api_delete', kwargs={'pk': circuit.pk}),
        'is_admin_created': circuit.is_admin_created,
        'is_admin': is_admin(request)
    }

def json_error(message, status=400):
    return JsonResponse({"ok": False, "error": message}, status=status)

# ================== Page Views ==================
@require_GET
def circuit_list_page(request):
    """Merender halaman utama yang akan mengambil data via JavaScript."""
    return render(request, "circuit_list.html")

@require_GET
def circuit_detail_page(request, pk):
    """Merender halaman detail untuk satu sirkuit."""
    circuit = get_object_or_404(Circuit, pk=pk)
    return render(request, "circuit_detail.html", {"circuit": circuit})

def add_circuit_page(request):
    """Merender halaman dengan form untuk menambah sirkuit baru."""
    if not is_admin(request):
        return HttpResponseForbidden("You are not authorized to add a circuit.")
    form = CircuitForm()
    return render(request, 'add_circuit.html', {'form': form, 'page_title': 'Add New Circuit'}) 

def edit_circuit_page(request, pk):
    """Merender halaman dengan form untuk mengedit sirkuit yang ada."""
    if not is_admin(request):
        return HttpResponseForbidden("You are not authorized to edit this circuit.")
    circuit = get_object_or_404(Circuit, pk=pk)
    form = CircuitForm(instance=circuit)
    return render(request, "edit_circuit.html", {"form": form, "circuit": circuit, 'page_title': f'Edit {circuit.name}'})


# ================== API Views ==================
@require_GET
def api_circuit_list(request):
    """Endpoint API untuk mendapatkan daftar sirkuit."""
    try:
        circuits_qs = Circuit.objects.all().order_by('name')
        data = [serialize_circuit(c, request) for c in circuits_qs]
        return JsonResponse({"ok": True, "data": data})
    except Exception as e:
        traceback.print_exc() 
        return json_error(f"Server error: {e}", status=500)

@csrf_protect
@login_required
@require_POST
def web_circuit_create(request):
    if not is_admin(request):
        return HttpResponseForbidden("Admin role required.")

    form = CircuitForm(request.POST)
    if form.is_valid():
        circuit = form.save(commit=False)
        circuit.is_admin_created = True
        circuit.save()
        return HttpResponseRedirect(reverse("circuit:list_page"))
    else:
        return render(request, "add_circuit.html", {"form": form, 'page_title': 'Add New Circuit'})


@csrf_protect
@csrf_protect
@login_required
@require_POST
def web_circuit_update(request, pk):
    if not is_admin(request):
        return HttpResponseForbidden("Admin role required.")

    circuit = get_object_or_404(Circuit, pk=pk)
    form = CircuitForm(request.POST, instance=circuit)
    
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse("circuit:list_page"))
    else:
        return render(request, "edit_circuit.html", {"form": form, "circuit": circuit, 'page_title': f'Edit {circuit.name}'})


@csrf_protect
@login_required
@require_POST
def web_circuit_delete(request, pk):
    if not is_admin(request):
        return HttpResponseForbidden("Admin role required.")
    
    circuit = get_object_or_404(Circuit, pk=pk)
    circuit.delete()
    return HttpResponseRedirect(reverse("circuit:list_page"))

@csrf_exempt
@require_POST
def api_circuit_create(request):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "message": "Authentication required"}, status=401)

    try:
        data = json.loads(request.body)
        
        if not data.get('name') or not data.get('country'):
             return JsonResponse({"ok": False, "message": "Name and Country are required."}, status=400)

        new_circuit = Circuit.objects.create(
            name=data.get('name'),
            map_image_url=data.get('map_image_url', ''),
            location=data.get('location', ''),
            country=data.get('country'),
            circuit_type=data.get('circuit_type', 'RACE'),
            direction=data.get('direction', 'CW'),
            length_km=float(data.get('length_km') or 0),
            turns=int(data.get('turns') or 0),
            grands_prix=data.get('grands_prix', ''),
            seasons=data.get('seasons', ''),
            grands_prix_held=int(data.get('grands_prix_held') or 0),
            is_admin_created=True
        )
        return JsonResponse({"ok": True, "message": "Circuit created successfully"})

    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)}, status=500)

@csrf_exempt
@require_POST
def api_circuit_update(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "message": "Authentication required"}, status=401)

    try:
        circuit = get_object_or_404(Circuit, pk=pk)
        data = json.loads(request.body)

        circuit.name = data.get('name', circuit.name)
        circuit.map_image_url = data.get('map_image_url', circuit.map_image_url)
        circuit.location = data.get('location', circuit.location)
        circuit.country = data.get('country', circuit.country)
        circuit.circuit_type = data.get('circuit_type', circuit.circuit_type)
        circuit.direction = data.get('direction', circuit.direction)
        circuit.length_km = float(data.get('length_km', circuit.length_km))
        circuit.turns = int(data.get('turns', circuit.turns))
        circuit.grands_prix = data.get('grands_prix', circuit.grands_prix)
        circuit.seasons = data.get('seasons', circuit.seasons)
        circuit.grands_prix_held = int(data.get('grands_prix_held', circuit.grands_prix_held))
        
        circuit.save()
        return JsonResponse({"ok": True, "message": "Circuit updated successfully"})

    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)}, status=500)

@csrf_exempt
@require_POST
def api_circuit_delete(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "message": "Authentication required"}, status=401)
    
    try:
        circuit = get_object_or_404(Circuit, pk=pk)
        circuit.delete()
        return JsonResponse({"ok": True, "message": "Circuit deleted"})
    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)}, status=500)