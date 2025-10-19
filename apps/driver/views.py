# from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
# from django.urls import reverse_lazy
# from django.http import HttpResponse
# from django.core import serializers

# from .models import Driver
# from .forms import DriverForm

# class DriverList(ListView):
#     model = Driver
#     template_name = 'driver/driver_list.html'
#     context_object_name = 'object_list'
#     ordering = ['driver_number']

# class DriverDetail(DetailView):
#     model = Driver
#     template_name = 'driver/driver_detail.html'

# class DriverCreate(CreateView):
#     model = Driver
#     form_class = DriverForm
#     template_name = 'driver/driver_form.html'
#     success_url = reverse_lazy('driver:driver_list')

# class DriverUpdate(UpdateView):
#     model = Driver
#     form_class = DriverForm
#     template_name = 'driver/driver_form.html'
#     success_url = reverse_lazy('driver:driver_list')

# class DriverDelete(DeleteView):
#     model = Driver
#     template_name = 'driver/driver_confirm_delete.html'
#     success_url = reverse_lazy('driver:driver_list')

# # ===== XML / JSON (Driver only) =====
# def show_xml(request):
#     xml_data = serializers.serialize("xml", Driver.objects.all())
#     return HttpResponse(xml_data, content_type="application/xml")

# def show_json(request):
#     json_data = serializers.serialize("json", Driver.objects.all())
#     return HttpResponse(json_data, content_type="application/json")

# def show_xml_by_id(request, driver_number):
#     qs = Driver.objects.filter(pk=driver_number)
#     if not qs.exists():
#         return HttpResponse(status=404)
#     xml_data = serializers.serialize("xml", qs)
#     return HttpResponse(xml_data, content_type="application/xml")

# def show_json_by_id(request, driver_number):
#     try:
#         obj = Driver.objects.get(pk=driver_number)
#     except Driver.DoesNotExist:
#         return HttpResponse(status=404)
#     json_data = serializers.serialize("json", [obj])
#     return HttpResponse(json_data, content_type="application/json")

# apps/driver/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.core import serializers

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Driver
from .forms import DriverForm

# ------ akses publik ------
class DriverList(ListView):
    model = Driver
    template_name = 'driver/driver_list.html'
    context_object_name = 'object_list'
    ordering = ['driver_number']

class DriverDetail(DetailView):
    model = Driver
    template_name = 'driver/driver_detail.html'

# ------ helper untuk write-protected ------
class StaffRequiredMixin(UserPassesTestMixin):
    login_url = '/accounts/login/'  # arahkan ke modul user tim kamu
    redirect_field_name = 'next'

    def test(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    # Untuk Django baru, override test_func:
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

# ------ CRUD: wajib login + staff ------
class DriverCreate(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Driver
    form_class = DriverForm
    template_name = 'driver/driver_form.html'
    success_url = reverse_lazy('driver:driver_list')
    login_url = '/accounts/login/'

class DriverUpdate(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Driver
    form_class = DriverForm
    template_name = 'driver/driver_form.html'
    success_url = reverse_lazy('driver:driver_list')
    login_url = '/accounts/login/'

class DriverDelete(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Driver
    template_name = 'driver/driver_confirm_delete.html'
    success_url = reverse_lazy('driver:driver_list')
    login_url = '/accounts/login/'

# ------ XML/JSON endpoints (pilih kebijakan) ------
# Jika ingin publik: biarkan seperti ini.
# Jika ingin hanya staff, bungkus dengan @staff_member_required atau cek request.user di view.
def show_xml(request):
    data = Driver.objects.all()
    xml_data = serializers.serialize("xml", data)
    return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    data = Driver.objects.all()
    json_data = serializers.serialize("json", data)
    return HttpResponse(json_data, content_type="application/json")

def show_xml_by_id(request, driver_number):
    qs = Driver.objects.filter(pk=driver_number)
    if not qs.exists():
        return HttpResponse(status=404)
    xml_data = serializers.serialize("xml", qs)
    return HttpResponse(xml_data, content_type="application/xml")

def show_json_by_id(request, driver_number):
    try:
        obj = Driver.objects.get(pk=driver_number)
    except Driver.DoesNotExist:
        return HttpResponse(status=404)
    json_data = serializers.serialize("json", [obj])
    return HttpResponse(json_data, content_type="application/json")
