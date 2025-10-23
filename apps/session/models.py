from django.db import models


class Session(models.Model):
    session_key = models.IntegerField(primary_key=True)
    meeting_key = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=120, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["session_key"]

    def __str__(self) -> str:
        label = self.name or ""
        suffix = label.upper() if label else "SESSION"
        return f"{self.session_key} - {suffix}" if label else str(self.session_key)
