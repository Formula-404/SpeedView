from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("session", "0002_alter_session_meeting"),
    ]

    operations = [
        migrations.RenameField(
            model_name="session",
            old_name="meeting",
            new_name="meeting_key",
        ),
        migrations.AlterField(
            model_name="session",
            name="meeting_key",
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True),
        ),
    ]

