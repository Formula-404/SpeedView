from django.db import models
from django.urls import reverse

class Team(models.Model):
    team_name = models.CharField(max_length=255, primary_key=True)

    short_code = models.CharField(max_length=8, blank=True)
    team_logo_url = models.TextField(default='https://www.edigitalagency.com.au/wp-content/uploads/F1-logo-png-medium-size.png')
    website = models.URLField(blank=True)
    wiki_url = models.URLField(blank=True)

    team_colour = models.CharField(max_length=6)
    team_colour_secondary = models.CharField(max_length=6, blank=True)

    country = models.CharField(max_length=64, blank=True)
    base = models.CharField(max_length=128, blank=True)
    founded_year = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    team_description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.team_name

    def get_absolute_url(self):
        return reverse("team:detail_page", kwargs={"team_name": self.pk})