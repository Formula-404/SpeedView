from django.db import migrations, models
import django.db.models.deletion


def ensure_related(apps, schema_editor):
    Car = apps.get_model("car", "Car")
    Meeting = apps.get_model("meeting", "Meeting")
    Session = apps.get_model("session", "Session")

    meeting_values = (
        Car.objects.exclude(meeting_key__isnull=True)
        .values_list("meeting_key", flat=True)
        .distinct()
    )
    for mk in meeting_values:
        Meeting.objects.get_or_create(meeting_key=mk)

    session_values = (
        Car.objects.exclude(session_key__isnull=True)
        .values_list("session_key", "meeting_key")
        .distinct()
    )
    for sk, mk in session_values:
        meeting = Meeting.objects.filter(meeting_key=mk).first()
        session, created = Session.objects.get_or_create(
            session_key=sk,
            defaults={"meeting": meeting},
        )
        if meeting and session.meeting_id is None:
            session.meeting = meeting
            session.save(update_fields=["meeting"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("meeting", "0001_initial"),
        ("session", "0001_initial"),
        ("car", "0008_car_brake_choices"),
    ]

    operations = [
        migrations.RunPython(ensure_related, noop),
        migrations.AlterField(
            model_name="car",
            name="meeting_key",
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_column="meeting_key",
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cars",
                to="meeting.meeting",
                to_field="meeting_key",
            ),
        ),
        migrations.AlterField(
            model_name="car",
            name="session_key",
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_column="session_key",
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cars",
                to="session.session",
                to_field="session_key",
            ),
        ),
    ]
