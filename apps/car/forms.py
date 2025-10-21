from django.forms import ModelForm
from apps.car.models import Car


class CarForm(ModelForm):
    class Meta:
        model = Car
        fields = ["brake", "date", "driver_number", "drs", "meeting_key", "n_gear", "rpm", "session_key", "speed", "throttle"]

