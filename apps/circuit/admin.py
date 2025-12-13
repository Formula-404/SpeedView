from django.contrib import admin
from .models import Circuit

@admin.register(Circuit)
class CircuitAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'location', 'circuit_type', 'is_admin_created')
    search_fields = ('name', 'country', 'location')
    list_filter = ('circuit_type', 'country', 'is_admin_created') 
    ordering = ('name',)

    fieldsets = (
        ('Informasi Utama', {'fields': ('name', 'country', 'location')}),
        ('Gambar Peta', {'fields': ('map_image_url',)}), 
        ('Spesifikasi Trek', {'fields': ('circuit_type', 'direction', 'length_km', 'turns')}),
        ('Histori Grand Prix', {'fields': ('grands_prix', 'seasons', 'grands_prix_held')}),
    )

    # Otomatis set is_admin_created=True saat menyimpan via admin
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

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
