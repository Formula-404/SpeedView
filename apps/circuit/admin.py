from django.contrib import admin
from .models import Circuit
from django.utils.html import format_html

@admin.register(Circuit)
class CircuitAdmin(admin.ModelAdmin):
    """
    Kustomisasi tampilan admin untuk model Circuit.
    """
    list_display = ('name', 'country', 'circuit_type', 'length_km', 'last_used', 'image_preview')
    search_fields = ('name', 'country', 'location', 'grands_prix')
    list_filter = ('country', 'circuit_type', 'direction')
    
    # Mengelompokkan field agar form admin lebih rapi
    fieldsets = (
        ('Informasi Utama', {
            'fields': ('name', 'country', 'location')
        }),
        ('Input Gambar (via URL)', {
            'description': "Tempel URL gambar peta sirkuit di sini. Gambar akan diunduh saat disimpan.",
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
    def image_preview(self, obj):
        """
        Membuat tag HTML <img> untuk menampilkan preview gambar yang sudah diunduh
        """
        if obj.map_image_file:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="200" style="border-radius: 8px;" /></a>', obj.map_image_file.url)
        return "(Tidak ada gambar)"
    
    # Memberi judul pada kolom preview gambar di halaman admin.
    image_preview.short_description = 'Preview Peta Sirkuit'