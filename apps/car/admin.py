from django.contrib import admin
from .models import Car

class ReadOnlyMixin:
    actions = None
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def has_view_permission(self, request, obj=None):
        return True
    def get_readonly_fields(self, request, obj=None):
        names = [f.name for f in self.model._meta.fields]
        names += [m.name for m in self.model._meta.many_to_many]
        return tuple(sorted(set(names + list(getattr(self, 'readonly_fields', [])))))

@admin.register(Car)
class CarAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'driver_number', 'session_key', 'meeting_key', 'date', 'speed', 'rpm', 'n_gear', 'throttle', 'brake', 'drs', 'is_manual')
    list_filter = ('is_manual', 'drs', 'n_gear', 'session_key', 'meeting_key', 'driver_number')
    search_fields = ('driver_number', 'session_key', 'meeting_key')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-date',)
    list_display_links = None
