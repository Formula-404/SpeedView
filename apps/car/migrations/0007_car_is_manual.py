from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("car", "0006_car_car_session_driver_ts_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="car",
            name="is_manual",
            field=models.BooleanField(default=False, editable=False, db_index=True),
        ),
    ]
