import uuid
from django.db import models
from apps.driver.models import Driver

class Laps(models.Model):
    """
    Data performa per lap (READ-ONLY).
    Unik per driver + session + lap_number.
    """
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver        = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='laps')
    meeting_key   = models.IntegerField()
    session_key   = models.IntegerField()

    date_start    = models.DateTimeField()
    lap_number    = models.PositiveIntegerField()

    duration_sector_1 = models.DurationField(null=True, blank=True)
    duration_sector_2 = models.DurationField(null=True, blank=True)
    duration_sector_3 = models.DurationField(null=True, blank=True)
    lap_duration      = models.DurationField(null=True, blank=True)

    i1_speed   = models.FloatField(null=True, blank=True)
    i2_speed   = models.FloatField(null=True, blank=True)
    st_speed   = models.FloatField(null=True, blank=True)

    segments_sector_1 = models.PositiveSmallIntegerField(null=True, blank=True)
    segments_sector_2 = models.PositiveSmallIntegerField(null=True, blank=True)
    segments_sector_3 = models.PositiveSmallIntegerField(null=True, blank=True)

    is_out_lap     = models.BooleanField(default=False)
    is_pit_out_lap = models.BooleanField(default=False)

    class Meta:
        db_table = 'laps'
        constraints = [
            models.UniqueConstraint(
                fields=['driver', 'session_key', 'lap_number'],
                name='uniq_lap_per_driver_session'
            )
        ]
        ordering = ['driver__driver_number', 'lap_number']

    def __str__(self):
        return f"Lap {self.lap_number} · #{self.driver_id} · S{self.session_key}"
