from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("meeting", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Session",
            fields=[
                ("session_key", models.IntegerField(primary_key=True, serialize=False)),
                ("name", models.CharField(blank=True, max_length=120)),
                ("start_time", models.DateTimeField(blank=True, null=True)),
                (
                    "meeting",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        db_column="meeting_key",
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sessions",
                        to="meeting.meeting",
                        to_field="meeting_key",
                    ),
                ),
            ],
            options={
                "ordering": ["session_key"],
            },
        ),
    ]
