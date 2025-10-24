from django.contrib import admin
from .models import Circuit
from django.utils.html import format_html

@admin.register(Circuit)
class CircuitAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'location', 'circuit_type', 'length_km')
    list_filter = ('circuit_type', 'direction', 'country')
    search_fields = ('name', 'location', 'country')
    ordering = ('name',)

    fieldsets = (
        ('Informasi Utama', {
            'fields': ('name', 'country', 'location')
        }),
        ('Input Gambar (via URL)', {
            'description': "Tempel URL gambar peta sirkuit di sini.",
            'fields': ('map_image_url', 'image_preview')
        }),
        ('Spesifikasi Trek', {
            'fields': ('circuit_type', 'direction', 'length_km', 'turns')
        }),
        ('Histori Grand Prix', {
            'fields': ('grands_prix', 'seasons', 'grands_prix_held', 'last_used')
        }),
    )

    readonly_fields = ('image_preview',)

    @admin.display(description='Preview Peta Sirkuit')
    def image_preview(self, obj):
        if obj.map_image_file:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="200" style="border-radius: 8px;" /></a>', obj.map_image_file.url)
        return "(Tidak ada gambar)"