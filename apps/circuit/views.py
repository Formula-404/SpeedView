from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Circuit

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin ini memastikan hanya pengguna dengan peran 'admin' yang bisa mengakses view.
    Jika tidak, pengguna akan diarahkan ke halaman daftar sirkuit.
    """
    def test_func(self):
        return (hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'admin')

# --- Views untuk semua pengguna (Read-Only) ---
class CircuitList(ListView):
    """Menampilkan daftar semua sirkuit"""
    model = Circuit
    template_name = 'circuit_list.html'
    context_object_name = 'circuits'
    paginate_by = 10  # Menampilkan 10 sirkuit per halaman
    ordering = ['name'] # Mengurutkan sirkuit berdasarkan nama

class CircuitDetail(DetailView):
    """Menampilkan detail dari satu sirkuit"""
    model = Circuit
    template_name = 'circuit_detail.html'
    context_object_name = 'circuit'

# --- Views hanya untuk Admin (CRUD) ---
class CircuitCreate(AdminRequiredMixin, CreateView):
    """Halaman form untuk membuat sirkuit baru"""
    model = Circuit
    template_name = 'circuit_form.html'
    fields = [
        'name', 'country', 'location', 'map_image_url', 
        'circuit_type', 'direction', 'length_km', 'turns',
        'grands_prix', 'seasons', 'grands_prix_held', 'last_used'
    ]
    success_url = reverse_lazy('circuit:circuit_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tambah Sirkuit Baru'
        return context

class CircuitUpdate(AdminRequiredMixin, UpdateView):
    """Halaman form untuk mengedit sirkuit yang ada"""
    model = Circuit
    template_name = 'circuit_form.html'
    fields = [
        'name', 'country', 'location', 'map_image_url', 
        'circuit_type', 'direction', 'length_km', 'turns',
        'grands_prix', 'seasons', 'grands_prix_held', 'last_used'
    ]
    success_url = reverse_lazy('circuit:circuit_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Sirkuit: {self.object.name}'
        return context

class CircuitDelete(AdminRequiredMixin, DeleteView):
    """Halaman konfirmasi untuk menghapus sirkuit"""
    model = Circuit
    template_name = 'circuit_confirm_delete.html'
    success_url = reverse_lazy('circuit:circuit_list')