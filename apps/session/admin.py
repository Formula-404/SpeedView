from django.contrib import admin
from .models import Session

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

@admin.register(Session)
class SessionAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('session_key', 'meeting_key', 'name', 'start_time')
    list_filter = ('meeting_key', 'name')
    search_fields = ('session_key', 'meeting_key', 'name')
    ordering = ('-start_time',)
    list_display_links = None
