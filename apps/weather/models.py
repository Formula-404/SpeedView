from django.db import models
from apps.meeting.models import Meeting

class Weather(models.Model):
    id = models.AutoField(primary_key=True)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="weather_entries",null=True)
    date = models.DateTimeField(db_index=True)
    air_temperature = models.FloatField(null=True, blank=True)
    track_temperature = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    wind_direction = models.IntegerField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    rainfall = models.BooleanField(default=False)

    class Meta:
        ordering = ['date']
        unique_together = ('meeting', 'date')

    def __str__(self):
        return f"Weather at {self.date} for {self.meeting.meeting_name}"