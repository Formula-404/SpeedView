from django.db import models


class Pit(models.Model):
    """
    Model Pit untuk menyimpan informasi tentang pit stop per lap.
    Model ini merupakan weak entity yang bergantung pada relasi dengan Laps, Session, Meeting, dan Driver.
    Hanya read-only (data diambil dari API atau sumber lain).
    """
    
    # ForeignKey untuk relasi ke Laps
    lap = models.ForeignKey(
        "laps.Laps", 
        on_delete=models.CASCADE, 
        related_name="pits", 
        help_text="Lap yang terkait dengan pit stop ini."
    )
    
    # ForeignKey untuk relasi ke Session
    session = models.ForeignKey(
        "session.Session", 
        on_delete=models.CASCADE, 
        related_name="pits", 
        help_text="Session tempat pit stop ini terjadi."
    )

    # ForeignKey untuk relasi ke Driver
    driver = models.ForeignKey(
        "driver.Driver", 
        on_delete=models.CASCADE, 
        related_name="pits", 
        help_text="Driver yang melakukan pit stop ini."
    )

    # ForeignKey untuk relasi ke Meeting (per session)
    meeting = models.ForeignKey(
        "meeting.Meeting", 
        on_delete=models.CASCADE, 
        related_name="pits", 
        help_text="Meeting tempat pit stop ini terjadi."
    )

    # Durasi pit stop (dalam detik)
    pit_duration = models.FloatField(
        help_text="Durasi pit stop (dalam detik).",
        editable=False
    )

    # Tanggal dan waktu saat pit stop
    date = models.DateTimeField(
        help_text="Tanggal dan waktu saat pit stop (dalam format ISO 8601).",
        editable=False
    )

    # Lap number untuk pit stop
    lap_number = models.PositiveSmallIntegerField(
        help_text="Nomor lap tempat pit stop ini terjadi.",
        editable=False
    )

    class Meta:
        db_table = "pit"
        ordering = ["lap_number"]
        # Menambahkan constraint untuk memastikan satu pit per lap dalam session
        constraints = [
            models.UniqueConstraint(
                fields=["driver", "session", "lap_number"],
                name="unique_driver_session_lap_number_for_pit"
            )
        ]

    def __str__(self):
        return f"Pit stop for Driver {self.driver.driver_number} in Lap {self.lap_number}"

    # Menghapus metode save agar tidak bisa mengubah data
    def save(self, *args, **kwargs):
        raise NotImplementedError("This model is read-only. Save operation is not allowed.")
