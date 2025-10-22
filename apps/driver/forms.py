from django.forms import ModelForm
from .models import Driver

class DriverForm(ModelForm):
    class Meta:
        model = Driver
        fields = [
            'driver_number', 'first_name', 'last_name', 'full_name',
            'broadcast_name', 'name_acronym', 'country_code',
            'headshot_url', 'team_name', 'meeting_key', 'session_key'
        ]
