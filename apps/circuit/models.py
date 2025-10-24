from django.db import models

class Circuit(models.Model):
    # Tipe sirkuit (pilihan tetap)
    CIRCUIT_TYPES = [
        ('STREET', 'Street circuit'),
        ('ROAD', 'Road circuit'),
        ('RACE', 'Race circuit'),
    ]

    # Arah sirkuit
    DIRECTIONS = [
        ('CW', 'Clockwise'),
        ('ACW', 'Anti-clockwise'),
    ]

    name = models.CharField("Circuit", max_length=255, unique=True)
    map_image_url = models.URLField("Map Image URL", max_length=1024, null=True, blank=True, help_text="Salin dan tempel URL gambar peta sirkuit di sini.")
    circuit_type = models.CharField("Type", max_length=10, choices=CIRCUIT_TYPES, default='RACE')
    direction = models.CharField("Direction", max_length=3, choices=DIRECTIONS, default='CW')
    location = models.CharField("Location", max_length=255)
    country = models.CharField("Country", max_length=100)
    last_used = models.IntegerField("Last used", null=True, blank=True, help_text="Tahun terakhir sirkuit digunakan di F1")
    length_km = models.FloatField("Length (km)", help_text="Panjang sirkuit dalam kilometer")
    turns = models.IntegerField("Turns")
    grands_prix = models.CharField("Grands Prix", max_length=255, help_text="Nama Grand Prix yang diadakan di sini")
    seasons = models.CharField("Season(s)", max_length=255, help_text="Contoh: 1985–1995, 2023")
    grands_prix_held = models.IntegerField("Grands Prix held")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Circuit"
        verbose_name_plural = "Circuits"