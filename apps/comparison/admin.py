from django.contrib import admin
from .models import Comparison, ComparisonTeam, ComparisonCircuit, ComparisonDriver, ComparisonCar

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

@admin.register(Comparison)
class ComparisonAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'owner', 'module', 'title', 'is_public', 'created_at')
    list_filter = ('module', 'is_public', 'created_at')
    search_fields = ('id', 'title', 'owner__username', 'owner__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_display_links = None

@admin.register(ComparisonTeam)
class ComparisonTeamAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'comparison', 'team', 'order_index')
    list_filter = ('comparison', 'team')
    search_fields = ('comparison__id', 'team__team_name')
    ordering = ('comparison', 'order_index')
    list_display_links = None

@admin.register(ComparisonCircuit)
class ComparisonCircuitAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'comparison', 'circuit', 'order_index')
    list_filter = ('comparison', 'circuit')
    search_fields = ('comparison__id', 'circuit__name')
    ordering = ('comparison', 'order_index')
    list_display_links = None

@admin.register(ComparisonDriver)
class ComparisonDriverAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'comparison', 'driver', 'order_index')
    list_filter = ('comparison', 'driver')
    search_fields = ('comparison__id', 'driver__driver_number', 'driver__full_name')
    ordering = ('comparison', 'order_index')
    list_display_links = None

@admin.register(ComparisonCar)
class ComparisonCarAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'comparison', 'car', 'order_index')
    list_filter = ('comparison',)
    search_fields = ('comparison__id', 'car__driver_number')
    ordering = ('comparison', 'order_index')
    list_display_links = None
