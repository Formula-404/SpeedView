import json
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect
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
    circuit = get_object_or_404(Circuit, pk=pk, is_admin_created=True)
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
@require_POST
def api_circuit_create(request):
    """Endpoint API untuk membuat sirkuit baru."""
    if not is_admin(request):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
             return json_error("Admin role required.", status=403)
        else:
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
@require_POST
def api_circuit_update(request, pk):
    """Endpoint API untuk memperbarui sirkuit yang ada."""
    if not is_admin(request):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return json_error("Admin role required.", status=403)
        else:
            return HttpResponseForbidden("Admin role required.")
    circuit = get_object_or_404(Circuit, pk=pk, is_admin_created=True) 
    form = CircuitForm(request.POST, instance=circuit)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse("circuit:list_page"))
    else:
        return render(request, "edit_circuit.html", {"form": form, "circuit": circuit, 'page_title': f'Edit {circuit.name}'})


@csrf_protect
@require_POST
def api_circuit_delete(request, pk):
    """Endpoint API untuk menghapus sirkuit."""
    if not is_admin(request):
        return json_error("Admin role required.", status=403) 
    try:
        circuit = get_object_or_404(Circuit, pk=pk, is_admin_created=True)
        circuit_name = circuit.name
        circuit.delete()
        return JsonResponse({"ok": True, "message": f"Circuit '{circuit_name}' deleted."})
    except Exception as e:
        traceback.print_exc() 
        return json_error(f"Error deleting circuit: {e}", status=500)