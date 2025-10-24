from django.contrib import admin
from .models import Session

class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [field.name for field in self.model._meta.fields]
        return []

@admin.register(Session)
class SessionAdmin(ReadOnlyModelAdmin):
    list_display = ("session_key", "meeting_key", "name", "start_time")
    list_filter = ("meeting_key",)
    search_fields = ("session_key", "meeting_key", "name")
    ordering = ("session_key",)
    readonly_fields = ("session_key", "meeting_key", "name", "start_time")
