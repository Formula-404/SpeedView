import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse

class Comparison(models.Model):
    MODULE_TEAM = "team"
    MODULE_CAR = "car"
    MODULE_DRIVER = "driver"
    MODULE_CIRCUIT = "circuit"
    MODULE_CHOICES = [
        (MODULE_TEAM, "Team"),
        (MODULE_CAR, "Car"),
        (MODULE_DRIVER, "Driver"),
        (MODULE_CIRCUIT, "Circuit"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comparisons")
    module = models.CharField(max_length=16, choices=MODULE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("comparison:detail_page", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.module} comparison {self.pk}"

class ComparisonTeam(models.Model):
    comparison = models.ForeignKey(Comparison, on_delete=models.CASCADE, related_name="team_links")
    team = models.ForeignKey("team.Team", on_delete=models.CASCADE)
    order_index = models.PositiveSmallIntegerField(default=0)
