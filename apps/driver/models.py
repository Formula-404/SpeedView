from django.db import models
from django.urls import reverse

class Driver(models.Model):
    """
    Entitas utama Driver. Primary key = driver_number.
    Catatan:
    - Relasi ke Session TIDAK lagi pakai FK/M2M. Kita simpan session_key (int) di DriverEntry.
    - Relasi ke Team: M2M via DriverTeam (kontrak/riwayat tim).
    - Model lain (car, laps, pit) cukup FK ke Driver (driver_number).
    """
    driver_number = models.PositiveSmallIntegerField(primary_key=True)

    # Identitas dasar
    first_name = models.CharField(max_length=64, blank=True)
    last_name = models.CharField(max_length=64, blank=True)
    full_name = models.CharField(max_length=128, blank=True)
    broadcast_name = models.CharField(
        max_length=128,
        blank=True,
        help_text="Nama yang ditampilkan di siaran/TV."
    )
    name_acronym = models.CharField(
        max_length=3,
        blank=True,
        help_text="Tiga huruf akronim (contoh: VER, HAM)."
    )
    country_code = models.CharField(max_length=3, blank=True)
    headshot_url = models.URLField(blank=True)

    # Relasi Many-to-Many ke Team via DriverTeam
    teams = models.ManyToManyField(
        "team.Team",
        through="DriverTeam",
        related_name="drivers",
        blank=True,
    )

    debut_meeting = models.ForeignKey(
        "meeting.Meeting",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drivers_debuted",
        help_text="Meeting pertama (opsional, ringkasan riwayat)."
    )
    biography = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "driver"
        ordering = ["driver_number"]

    def __str__(self):
        name = self.broadcast_name or self.full_name or (self.first_name + " " + self.last_name).strip()
        return f"{self.driver_number} - {name}"

    def get_absolute_url(self):
        return reverse("driver:driver_detail", kwargs={"driver_number": self.pk})

    # Helper: daftar session_key yang pernah diikuti driver ini (distinct)
    @property
    def session_keys(self):
        return list(self.entries.values_list("session_key", flat=True).distinct())


class DriverEntry(models.Model):
    """
    Penghubung Driver <-> Session (M:N) + menyertakan Meeting.
    TIDAK ada FK ke Session; kita simpan session_key dari OpenF1.
    """
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name="entries",
    )

    # Ganti FK Session -> integer key
    session_key = models.PositiveIntegerField(
        db_index=True,
        null=True,         # ← tambah
        blank=True,        # ← tambah
        help_text="OpenF1 session_key.",
    )

    # Foreign key untuk meeting (kalau Meeting-mu model lokal; jika tidak, ubah ke meeting_key IntegerField)
    meeting = models.ForeignKey(
        "meeting.Meeting",
        on_delete=models.CASCADE,
        related_name="driver_entries",
        help_text="Meeting yang menaungi session ini."
    )

    # Snapshot atribut yang memang per-session/meeting
    team = models.ForeignKey(
        "team.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_entries",
        help_text="Tim yang dibela pada session ini."
    )
    team_colour = models.CharField(
        max_length=6,
        blank=True,
        help_text="Hex colour pada session ini (RRGGBB)."
    )

    # Metadata waktu dari API
    date_start = models.DateTimeField(null=True, blank=True)
    date_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "driver_entry"
        unique_together = (("driver", "session_key"),)
        indexes = [
            models.Index(fields=["driver", "session_key"]),
            models.Index(fields=["meeting"]),
        ]

    def __str__(self):
        return f"Entry #{self.driver_id} @ session {self.session_key}"


class DriverTeam(models.Model):
    """
    Penghubung Driver <-> Team (M:N).
    Dipakai untuk menyimpan riwayat kontrak/afiliasi tim lintas musim/meeting.
    """
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name="team_links",
    )
    team = models.ForeignKey(
        "team.Team",
        on_delete=models.CASCADE,
        related_name="driver_links",
    )

    # Opsional: periode kontrak/afiliasi
    start_meeting = models.ForeignKey(
        "meeting.Meeting",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_team_starts",
    )
    end_meeting = models.ForeignKey(
        "meeting.Meeting",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_team_ends",
    )

    # Snapshot properti visual yang sering berubah
    team_colour = models.CharField(max_length=6, blank=True)

    class Meta:
        db_table = "driver_team"
        unique_together = (("driver", "team", "start_meeting"),)
        indexes = [
            models.Index(fields=["driver", "team"]),
        ]

    def __str__(self):
        return f"{self.driver_id} ↔ {self.team_id}"
