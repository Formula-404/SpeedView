from django.contrib import admin
from .models import Meeting

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

@admin.register(Meeting)
class MeetingAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('meeting_key', 'meeting_name', 'circuit_short_name', 'country_name', 'year', 'date_start')
    list_filter = ('year', 'country_name', 'circuit_short_name')
    search_fields = ('meeting_key', 'meeting_name', 'circuit_short_name', 'country_name')
    ordering = ('-date_start',)
    list_display_links = None