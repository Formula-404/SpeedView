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
    engines = models.TextField(blank=True, help_text="Comma-separated engine supplier list")

    first_entry = models.ForeignKey(
        "meeting.Meeting",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teams_first_entered",
    )
    last_entry = models.ForeignKey(
        "meeting.Meeting",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teams_last_entered",
    )

    constructors_championships = models.PositiveSmallIntegerField(default=0)
    drivers_championships = models.PositiveSmallIntegerField(default=0)
    races_entered = models.PositiveIntegerField(default=0)
    race_victories = models.PositiveIntegerField(default=0)
    podiums = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    
    avg_lap_time_ms = models.FloatField(null=True, blank=True)
    best_lap_time_ms = models.IntegerField(null=True, blank=True)
    avg_pit_duration_ms = models.FloatField(null=True, blank=True)
    top_speed_kph = models.FloatField(null=True, blank=True)
    laps_completed = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.team_name

    def get_absolute_url(self):
        return reverse("team:detail_page", kwargs={"team_name": self.pk})