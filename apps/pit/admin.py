from django.contrib import admin
from .models import Pit

@admin.register(Pit)
class PitAdmin(admin.ModelAdmin):
    list_display = ('driver', 'session_key', 'lap_number', 'pit_duration', 'tire_in', 'tire_out')
    search_fields = ('driver__full_name', 'driver__driver_number', 'session_key')
    list_filter = ('session_key',)
    readonly_fields = [f.name for f in Pit._meta.fields]

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
