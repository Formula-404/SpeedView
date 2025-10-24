from django.contrib import admin
from .models import Circuit

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

@admin.register(Circuit)
class CircuitAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'country', 'location', 'circuit_type', 'direction', 'length_km', 'turns', 'grands_prix_held')
    list_filter = ('circuit_type', 'direction', 'country')
    search_fields = ('name', 'location', 'country', 'grands_prix')
    ordering = ('name',)
    list_display_links = None