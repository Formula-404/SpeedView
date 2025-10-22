from django.contrib import admin
from .models import Laps

@admin.register(Laps)
class LapsAdmin(admin.ModelAdmin):
    list_display = ('driver', 'session_key', 'lap_number', 'lap_duration')
    search_fields = ('driver__full_name', 'driver__driver_number', 'session_key')
    list_filter = ('session_key',)
    readonly_fields = [f.name for f in Laps._meta.fields]  # semua field read-only

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
