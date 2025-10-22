from django.db import models

class Meeting(models.Model):
    meeting_key = models.IntegerField(primary_key=True)