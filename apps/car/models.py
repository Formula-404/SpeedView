from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Car(models.Model):
    """Represents a single telemetry snapshot returned by the OpenF1 car_data API."""

    class DRSStatus(models.IntegerChoices):
        OFF = 0, "DRS off"
        OFF_VARIANT = 1, "DRS off"
        UNKNOWN_2 = 2, "Unknown"
        UNKNOWN_3 = 3, "Unknown"
        DETECTED = 8, "Detected (eligible once in activation zone)"
        UNKNOWN_9 = 9, "Unknown"
        ON = 10, "DRS on"
        ON_VARIANT = 12, "DRS on"
        UNKNOWN_13 = 13, "Unknown"
        ON_HIGH = 14, "DRS on"

    brake = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    date = models.DateTimeField(db_index=True)
    driver_number = models.PositiveSmallIntegerField(db_index=True)
    drs = models.PositiveSmallIntegerField(choices=DRSStatus.choices)
    meeting_key = models.PositiveIntegerField(db_index=True)
    n_gear = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(8)])
    rpm = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(20000)])
    session_key = models.PositiveIntegerField(db_index=True)
    speed = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(450)])
    throttle = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Car telemetry sample"
        verbose_name_plural = "Car telemetry samples"
        ordering = ["-date"]
        default_permissions = ("view",)
        permissions = [
            (
                "manage_car_records",
                "Can create, update, and delete car telemetry records",
            )
        ]
        indexes = [
            models.Index(
                fields=["session_key", "driver_number", "date"],
                name="car_session_driver_ts_idx",
            ),
            models.Index(
                fields=["meeting_key", "driver_number"],
                name="car_meeting_driver_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["session_key", "driver_number", "date"],
                name="unique_car_sample_per_timestamp",
            )
        ]

    def __str__(self) -> str: 
        return f"{self.driver_number} | {self.session_key} | {self.date:%Y-%m-%d %H:%M:%S}"

    @property
    def drs_state(self) -> str:
        """Return a human readable interpretation of the DRS flag."""
        return self.get_drs_display()