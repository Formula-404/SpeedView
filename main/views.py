from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import HttpResponse
from django.core import serializers

from .models import Driver
from .forms import DriverForm


# ========= Driver CRUD =========
class DriverList(ListView):
    model = Driver
    template_name = 'main/main.html'
    context_object_name = 'object_list'
    ordering = ['driver_number']


class DriverDetail(DetailView):
    model = Driver
    template_name = 'main/driver_detail.html'


class DriverCreate(CreateView):
    model = Driver
    form_class = DriverForm
    template_name = 'main/driver_form.html'
    success_url = reverse_lazy('main:driver_list')


class DriverUpdate(UpdateView):
    model = Driver
    form_class = DriverForm
    template_name = 'main/driver_form.html'
    success_url = reverse_lazy('main:driver_list')


class DriverDelete(DeleteView):
    model = Driver
    template_name = 'main/driver_confirm_delete.html'
    success_url = reverse_lazy('main:driver_list')


# ========= XML / JSON endpoints (Driver) =========
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
