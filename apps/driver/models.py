from django.db import models

class Driver(models.Model):
    """
    Menyimpan detail pembalap, kewarganegaraan, dan info ringkas.
    (CRUD diaktifkan)
    """
    driver_number = models.PositiveSmallIntegerField(primary_key=True)
    first_name     = models.CharField(max_length=60, blank=True)
    last_name      = models.CharField(max_length=60, blank=True)
    full_name      = models.CharField(max_length=120, blank=True)
    broadcast_name = models.CharField(max_length=120, blank=True)
    name_acronym   = models.CharField(max_length=8, blank=True)
    country_code   = models.CharField(max_length=3, blank=True)
    headshot_url   = models.URLField(blank=True)

    meeting_key    = models.IntegerField(null=True, blank=True)
    session_key    = models.IntegerField(null=True, blank=True)

    team_name      = models.CharField(max_length=80, blank=True)

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'driver'
        ordering  = ['driver_number']

    def __str__(self):
        label = self.full_name or self.broadcast_name or self.name_acronym
        return f"{self.driver_number} · {label or 'Driver'}"