from django.contrib import admin
from .models import Meeting

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

@admin.register(Meeting)
class MeetingAdmin(ReadOnlyAdmin):
    list_display = ('meeting_key', 'meeting_name', 'circuit_short_name', 'country_name', 'year', 'date_start')
    list_filter = ('year', 'country_name', 'circuit_short_name')
    search_fields = ('meeting_name', 'circuit_short_name', 'country_name')
    ordering = ('-date_start',)