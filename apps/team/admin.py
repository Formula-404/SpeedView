from django.contrib import admin
from .models import Team

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

@admin.register(Team)
class TeamAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('team_name', 'short_code', 'country', 'founded_year', 'is_active', 'constructors_championships', 'drivers_championships', 'race_victories', 'points')
    list_filter = ('is_active', 'country', 'founded_year')
    search_fields = ('team_name', 'short_code', 'country', 'base')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-points', 'team_name')
    list_display_links = None

    fieldsets = (
        ('Basic Information', {
            'fields': ('team_name', 'short_code', 'team_logo_url', 'website', 'wiki_url')
        }),
        ('Team Colors', {
            'fields': ('team_colour', 'team_colour_secondary')
        }),
        ('Location & History', {
            'fields': ('country', 'base', 'founded_year', 'is_active', 'team_description', 'engines')
        }),
        ('Entry Information', {
            'fields': ('first_entry', 'last_entry')
        }),
        ('Championships & Statistics', {
            'fields': ('constructors_championships', 'drivers_championships', 'races_entered', 'race_victories', 'podiums', 'points')
        }),
        ('Performance Metrics', {
            'fields': ('avg_lap_time_ms', 'best_lap_time_ms', 'avg_pit_duration_ms', 'top_speed_kph', 'laps_completed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
