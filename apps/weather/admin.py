from django.contrib import admin
from .models import Weather

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

@admin.register(Weather)
class WeatherAdmin(ReadOnlyAdmin):
    list_display = ('date', 'meeting', 'air_temperature', 'track_temperature', 'pressure', 'rainfall')
    list_filter = ('meeting__country_name', 'rainfall')
    search_fields = ('meeting__meeting_name',)
    ordering = ('-date',)