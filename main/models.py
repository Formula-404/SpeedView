import uuid
from django.db import models


class Driver(models.Model):
    """
    Menyimpan detail pembalap, kewarganegaraan, dan info ringkas.
    (CRUD diaktifkan)
    """
    driver_number = models.PositiveSmallIntegerField(primary_key=True)  # PK sesuai ERD
    first_name     = models.CharField(max_length=60, blank=True)
    last_name      = models.CharField(max_length=60, blank=True)
    full_name      = models.CharField(max_length=120, blank=True)
    broadcast_name = models.CharField(max_length=120, blank=True)
    name_acronym   = models.CharField(max_length=8, blank=True)         # VER, HAM, dll
    country_code   = models.CharField(max_length=3, blank=True)         # ISO-3
    headshot_url   = models.URLField(blank=True)

    # konteks event (mengikuti ERD)
    meeting_key    = models.IntegerField(null=True, blank=True)
    session_key    = models.IntegerField(null=True, blank=True)

    # info tim (boleh dikosongkan, nanti bisa diganti FK Team kalau ada)
    team_name      = models.CharField(max_length=80, blank=True)

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'driver'
        ordering  = ['driver_number']

    def __str__(self):
        return f"{self.driver_number} · {self.full_name or self.broadcast_name or self.name_acronym}"


class Laps(models.Model):
    """
    Data performa per lap (READ-ONLY di admin/view).
    Unik per driver + session + lap_number.
    """
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver        = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='laps')
    meeting_key   = models.IntegerField()
    session_key   = models.IntegerField()

    date_start    = models.DateTimeField()
    lap_number    = models.PositiveIntegerField()

    # sektor & waktu
    duration_sector_1 = models.DurationField(null=True, blank=True)
    duration_sector_2 = models.DurationField(null=True, blank=True)
    duration_sector_3 = models.DurationField(null=True, blank=True)
    lap_duration      = models.DurationField(null=True, blank=True)

    # kecepatan (opsional)
    i1_speed   = models.FloatField(null=True, blank=True)
    i2_speed   = models.FloatField(null=True, blank=True)
    st_speed   = models.FloatField(null=True, blank=True)  # speed trap

    # jumlah segmen per sektor (berdasarkan ERD)
    segments_sector_1 = models.PositiveSmallIntegerField(null=True, blank=True)
    segments_sector_2 = models.PositiveSmallIntegerField(null=True, blank=True)
    segments_sector_3 = models.PositiveSmallIntegerField(null=True, blank=True)

    # flags
    is_out_lap     = models.BooleanField(default=False)
    is_pit_out_lap = models.BooleanField(default=False)

    class Meta:
        db_table = 'laps'
        constraints = [
            models.UniqueConstraint(
                fields=['driver', 'session_key', 'lap_number'],
                name='uniq_lap_per_driver_session'
            )
        ]
        ordering = ['driver__driver_number', 'lap_number']

    def __str__(self):
        return f"Lap {self.lap_number} · #{self.driver_id} · S{self.session_key}"


class Pit(models.Model):
    """
    Data pit stop (READ-ONLY di admin/view).
    Unik per driver + session + lap_number.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver       = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='pitstops')
    meeting_key  = models.IntegerField()
    session_key  = models.IntegerField()

    date         = models.DateTimeField()
    lap_number   = models.PositiveIntegerField()
    pit_duration = models.DurationField(null=True, blank=True)

    # opsional strategi ban
    tire_in   = models.CharField(max_length=20, blank=True)
    tire_out  = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'pit'
        constraints = [
            models.UniqueConstraint(
                fields=['driver', 'session_key', 'lap_number'],
                name='uniq_pit_per_driver_session'
            )
        ]
        ordering = ['driver__driver_number', 'lap_number']

    def __str__(self):
        return f"Pit · Lap {self.lap_number} · #{self.driver_id} · S{self.session_key}"
