from django.db import models

class Team(models.Model):
    team_name = models.CharField(max_length=255, primary_key=True)
    team_colour = models.CharField(max_length=6)
    team_description = models.TextField(blank=True, null=True)