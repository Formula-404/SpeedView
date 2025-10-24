import json
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse
from .models import Circuit
from .forms import CircuitForm

# ================== Helpers ==================
def is_admin(request):
    """Mengecek apakah user terautentikasi dan punya role 'admin'."""
    if not request.user.is_authenticated:
        return False
    profile = getattr(request.user, "profile", None) 
    return getattr(profile, "role", None) == "admin"

def serialize_circuit(circuit: Circuit, request):
    """Mengubah objek Circuit menjadi dictionary yang aman untuk JSON."""
    return {
        "id": circuit.pk,
        "name": circuit.name,
        "country": circuit.country,
        "location": circuit.location,
        "map_image_url": circuit.map_image_url,
        'detail_url': reverse('circuit:detail_page', kwargs={'pk': circuit.pk}),
        'edit_url': reverse('circuit:edit_page', kwargs={'pk': circuit.pk}),
        'delete_url': reverse('circuit:api_delete', kwargs={'pk': circuit.pk}),
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
    """Endpoint API untuk mendapatkan daftar semua sirkuit."""
    try:
        circuits = Circuit.objects.all().order_by('name')
        data = [serialize_circuit(c, request) for c in circuits]
        return JsonResponse({"ok": True, "data": data})
    except Exception as e:
        return json_error(f"Server error: {e}", status=500)

@csrf_protect
@require_POST
def api_circuit_create(request):
    """Endpoint API untuk membuat sirkuit baru."""
    if not is_admin(request):
        return JsonResponse({"ok": False, "error": "Admin role required."}, status=403)
    
    form = CircuitForm(request.POST)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse("circuit:list_page"))
    return render(request, "add_circuit.html", {"form": form})

@csrf_protect
@require_POST
def api_circuit_update(request, pk):
    """Endpoint API untuk memperbarui sirkuit yang ada."""
    if not is_admin(request):
        return JsonResponse({"ok": False, "error": "Admin role required."}, status=403)

    circuit = get_object_or_404(Circuit, pk=pk)
    form = CircuitForm(request.POST, instance=circuit)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse("circuit:list_page"))    
    return render(request, "edit_circuit.html", {"form": form, "circuit": circuit})

@csrf_protect
@require_POST
def api_circuit_delete(request, pk):
    """Endpoint API untuk menghapus sirkuit."""
    if not is_admin(request):
        return JsonResponse({"ok": False, "error": "Admin role required."}, status=403)  
    try:
        circuit = get_object_or_404(Circuit, pk=pk)
        circuit_name = circuit.name
        circuit.delete()
        return JsonResponse({"ok": True, "message": f"Circuit '{circuit_name}' deleted."})
    except Exception as e:
        return json_error(f"Error deleting circuit: {e}", status=500)