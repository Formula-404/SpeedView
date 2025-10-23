from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("car", "0010_alter_car_meeting_key_alter_car_session_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="car",
            name="meeting_key",
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="car",
            name="session_key",
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True),
        ),
    ]
