from django.contrib import admin
from .models import Weather

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

@admin.register(Weather)
class WeatherAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'meeting', 'date', 'air_temperature', 'track_temperature', 'pressure', 'wind_speed', 'wind_direction', 'humidity', 'rainfall')
    list_filter = ('rainfall', 'meeting')
    search_fields = ('meeting__meeting_name', 'meeting__country_name')
    ordering = ('-date',)
    list_display_links = None