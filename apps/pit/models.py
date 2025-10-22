import uuid
from django.db import models
from apps.driver.models import Driver

class Pit(models.Model):
    """
    Data pit stop (READ-ONLY).
    Unik per driver + session + lap_number.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver       = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='pitstops')
    meeting_key  = models.IntegerField()
    session_key  = models.IntegerField()

    date         = models.DateTimeField()
    lap_number   = models.PositiveIntegerField()
    pit_duration = models.DurationField(null=True, blank=True)

    tire_in   = models.CharField(max_length=20, blank=True)
    tire_out  = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'pit'
        constraints = [
            models.UniqueConstraint(
                fields=['driver', 'session_key', 'lap_number'],
                name='uniq_pit_per_driver_session'
            )
        ]
        ordering = ['driver__driver_number', 'lap_number']

    def __str__(self):
        return f"Pit · Lap {self.lap_number} · #{self.driver_id} · S{self.session_key}"
