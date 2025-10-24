from django.db import models

class Meeting(models.Model):
    meeting_key = models.PositiveIntegerField(primary_key=True)
    meeting_name = models.CharField(max_length=255, null=True, blank=True)
    circuit_short_name = models.CharField(max_length=100, null=True, blank=True)
    country_name = models.CharField(max_length=100, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    date_start = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_start']

    def __str__(self):
        return f"{self.meeting_name} ({self.year})"
