from django.db import models
from django.urls import reverse

class Team(models.Model):
    team_name = models.CharField(max_length=255, primary_key=True)
    team_colour = models.CharField(max_length=6)
    team_description = models.TextField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse("team:detail_page", kwargs={"team_name": self.pk})