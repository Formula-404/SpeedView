from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.driver.models import Driver


class Car(models.Model):
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

    brake = models.PositiveSmallIntegerField(
        choices=[(0, "Off"), (100, "Full brake")],
    )
    date = models.DateTimeField(db_index=True)
    driver_number = models.PositiveSmallIntegerField(db_index=True)
    drs = models.PositiveSmallIntegerField(choices=DRSStatus.choices)
    meeting_key = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    n_gear = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(8)]
    )
    rpm = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20000)]
    )
    session_key = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    speed = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(450)]
    )
    throttle = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_manual = models.BooleanField(default=False, db_index=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    driver = models.ForeignKey(
        Driver,
        to_field="driver_number",
        db_column="driver",
        on_delete=models.CASCADE,
        related_name="cars",
        db_index=True,
        blank=True,
        default=None,
        null=True,
    )

    class Meta:
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

    def __str__(self) -> str:
        session_label = self.session_key or "?"
        return f"{self.driver_number} | {session_label} | {self.date:%Y-%m-%d %H:%M:%S}"

    @property
    def drs_state(self) -> str:
        return self.get_drs_display()

    @property
    def meeting_key_value(self) -> int | None:
        return self.meeting_key

    @property
    def session_key_value(self) -> int | None:
        return self.session_key
