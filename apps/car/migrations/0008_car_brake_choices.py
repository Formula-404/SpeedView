from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("car", "0007_car_is_manual"),
    ]

    operations = [
        migrations.AlterField(
            model_name="car",
            name="brake",
            field=models.PositiveSmallIntegerField(choices=[(0, "Off"), (100, "Full brake")]),
        ),
    ]
