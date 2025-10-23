from django.db import models

from apps.meeting.models import Meeting


class Session(models.Model):
    session_key = models.IntegerField(primary_key=True)
    meeting = models.ForeignKey(
        Meeting,
        db_column="meeting_key",
        to_field="meeting_key",
        null=True,
        blank=True,
        related_name="sessions",
        on_delete=models.SET_NULL,
    )
    name = models.CharField(max_length=120, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["session_key"]

    def __str__(self) -> str:
        label = self.name or ""
        suffix = label.upper() if label else "SESSION"
        return f"{self.session_key} - {suffix}" if label else str(self.session_key)
