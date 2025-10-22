from django.contrib import admin
from .models import Driver

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('driver_number','full_name','team_name','country_code')
    search_fields = ('full_name','broadcast_name','name_acronym','driver_number')
    ordering = ('driver_number',)
