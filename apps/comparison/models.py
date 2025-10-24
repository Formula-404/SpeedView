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
        ("team", "Team"),
        ("car", "Car"),
        ("driver", "Driver"),
        ("circuit", "Circuit"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comparisons")
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    title = models.CharField(max_length=100, default="My Comparison")
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("comparison:detail_page", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.module} comparison {self.pk}"

class ComparisonTeam(models.Model):
    comparison = models.ForeignKey(Comparison, on_delete=models.CASCADE, related_name="team_links")
    team = models.ForeignKey("team.Team", on_delete=models.CASCADE)
    order_index = models.PositiveSmallIntegerField(default=0)

class ComparisonCircuit(models.Model):
    comparison = models.ForeignKey(Comparison, on_delete=models.CASCADE, related_name="circuit_links")
    circuit = models.ForeignKey("circuit.Circuit", on_delete=models.CASCADE)
    order_index = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.comparison.id} → {self.circuit.id} ({self.order_index})"
    
class ComparisonDriver(models.Model):
    comparison = models.ForeignKey(Comparison, on_delete=models.CASCADE, related_name="driver_links")
    driver = models.ForeignKey("driver.Driver", on_delete=models.CASCADE)
    order_index = models.PositiveSmallIntegerField(default=0)


    def __str__(self):
        return f"{self.comparison.id} → {self.driver.driver_number} ({self.order_index})"


class ComparisonCar(models.Model):
    comparison = models.ForeignKey(Comparison, on_delete=models.CASCADE, related_name="car_links")
    car = models.ForeignKey("car.Car", on_delete=models.CASCADE)
    order_index = models.PositiveSmallIntegerField(default=0)


    def __str__(self):
        return f"{self.comparison.id} → {self.car} ({self.order_index})"