from django.contrib import admin
from .models import Driver, DriverEntry, DriverTeam

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

@admin.register(Driver)
class DriverAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('driver_number', 'full_name', 'broadcast_name', 'name_acronym', 'country_code', 'created_at', 'updated_at')
    list_filter = ('country_code',)
    search_fields = ('driver_number', 'first_name', 'last_name', 'full_name', 'broadcast_name', 'name_acronym')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('driver_number',)
    list_display_links = None

@admin.register(DriverEntry)
class DriverEntryAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'driver', 'session_key', 'meeting', 'team', 'team_colour', 'date_start', 'date_end')
    list_filter = ('meeting', 'team', 'driver')
    search_fields = ('driver__driver_number', 'session_key', 'meeting__meeting_name', 'team__team_name')
    ordering = ('-date_start',)
    list_display_links = None

@admin.register(DriverTeam)
class DriverTeamAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'driver', 'team', 'start_meeting', 'end_meeting', 'team_colour')
    list_filter = ('team', 'driver')
    search_fields = ('driver__driver_number', 'team__team_name')
    ordering = ('driver',)
    list_display_links = None
