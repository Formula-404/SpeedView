from django.db import models


class Laps(models.Model):
    """
    Model Laps untuk menyimpan informasi lap per driver per session.
    Model ini hanya read-only (data diambil dari API atau sumber lain).
    """
    
    # ForeignKey untuk relasi ke Driver
    driver = models.ForeignKey(
        "driver.Driver", 
        on_delete=models.CASCADE, 
        related_name="laps", 
        help_text="Driver yang melaju pada lap ini.",
        editable=False
    )

    # ForeignKey untuk relasi ke Session
    session = models.ForeignKey(
        "session.Session", 
        on_delete=models.CASCADE, 
        related_name="laps", 
        help_text="Session tempat lap ini terjadi.",
        editable=False
    )

    # ForeignKey untuk relasi ke Meeting (per session)
    meeting = models.ForeignKey(
        "meeting.Meeting", 
        on_delete=models.CASCADE, 
        related_name="laps", 
        help_text="Meeting tempat lap ini terjadi.",
        editable=False
    )

    # Unique identifier untuk setiap lap dalam sesi (lap_number)
    lap_number = models.PositiveSmallIntegerField(
        unique=True, 
        help_text="Nomor urut lap dalam session.",
        editable=False
    )

    # Waktu yang dibutuhkan untuk sektor lap (sumber dari API OpenF1)
    duration_sector_1 = models.FloatField(
        help_text="Waktu sektor 1 lap dalam detik.",
        editable=False
    )
    duration_sector_2 = models.FloatField(
        help_text="Waktu sektor 2 lap dalam detik.",
        editable=False
    )
    duration_sector_3 = models.FloatField(
        help_text="Waktu sektor 3 lap dalam detik.",
        editable=False
    )
    
    # Kecepatan pada sektor lap (sumber dari API OpenF1)
    i1_speed = models.FloatField(
        help_text="Kecepatan pada titik sektor 1 lap (km/h).",
        editable=False
    )
    i2_speed = models.FloatField(
        help_text="Kecepatan pada titik sektor 2 lap (km/h).",
        editable=False
    )

    # Status apakah lap keluar pit atau tidak (is_pit_out_lap)
    is_pit_out_lap = models.BooleanField(
        default=False,
        help_text="Menunjukkan apakah lap ini adalah lap keluar pit.",
        editable=False
    )

    # Total waktu lap
    lap_duration = models.FloatField(
        help_text="Total durasi lap dalam detik.",
        editable=False
    )

    # Mini-sectors (untuk setiap sektor lap)
    segments_sector_1 = models.JSONField(
        blank=True,
        null=True,
        help_text="Mini-sector untuk sektor 1 lap.",
        editable=False
    )
    segments_sector_2 = models.JSONField(
        blank=True,
        null=True,
        help_text="Mini-sector untuk sektor 2 lap.",
        editable=False
    )
    segments_sector_3 = models.JSONField(
        blank=True,
        null=True,
        help_text="Mini-sector untuk sektor 3 lap.",
        editable=False
    )

    # Waktu dan kecepatan di titik spesifik untuk kecepatan tinggi (speed trap)
    st_speed = models.FloatField(
        null=True,
        blank=True,
        help_text="Kecepatan di titik speed trap (km/h).",
        editable=False
    )

    # Relasi ke Pit
    pit = models.ForeignKey(
        "pit.Pit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laps",
        help_text="Relasi ke pit untuk lap ini.",
        editable=False
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = "laps"
        ordering = ["lap_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["driver", "session", "lap_number"],
                name="unique_driver_session_lap_number"
            )
        ]
    
    def __str__(self):
        return f"Lap {self.lap_number} by Driver {self.driver.driver_number} in Session {self.session.session_key}"

    # Menghapus metode save agar tidak bisa mengubah data
    def save(self, *args, **kwargs):
        raise NotImplementedError("This model is read-only. Save operation is not allowed.")
