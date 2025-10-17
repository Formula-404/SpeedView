from django.contrib import admin
from .models import Driver, Laps, Pit


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display  = ('driver_number', 'full_name', 'name_acronym', 'country_code',
                     'team_name', 'meeting_key', 'session_key')
    search_fields = ('full_name', 'broadcast_name', 'name_acronym', 'country_code', 'team_name')
    list_filter   = ('country_code', 'team_name')
    ordering      = ('driver_number',)


@admin.register(Laps)
class LapsAdmin(admin.ModelAdmin):
    list_display  = ('driver', 'session_key', 'lap_number', 'lap_duration', 'i1_speed', 'i2_speed', 'st_speed')
    list_filter   = ('session_key', 'driver')
    search_fields = ('driver__full_name', 'driver__name_acronym')
    readonly_fields = [f.name for f in Laps._meta.fields]

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(Pit)
class PitAdmin(admin.ModelAdmin):
    list_display  = ('driver', 'session_key', 'lap_number', 'pit_duration', 'tire_in', 'tire_out')
    list_filter   = ('session_key', 'driver')
    search_fields = ('driver__full_name', 'driver__name_acronym')
    readonly_fields = [f.name for f in Pit._meta.fields]

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
