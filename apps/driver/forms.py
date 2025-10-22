from django import forms
from .models import Driver

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        # Hanya menggunakan field yang ada di dalam model Driver
        fields = ["driver_number", "full_name", "broadcast_name", "country_code", "headshot_url", "teams"]

    def clean_driver_number(self):
        driver_number = self.cleaned_data.get("driver_number")
        if Driver.objects.filter(driver_number=driver_number).exists():
            raise forms.ValidationError("A driver with this number already exists.")
        return driver_number
