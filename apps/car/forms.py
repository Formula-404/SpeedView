from django import forms
from django.forms import ModelForm

from apps.car.models import Car
from apps.meeting.models import Meeting
from apps.session.models import Session


class CarForm(ModelForm):
    meeting_key = forms.IntegerField(required=False, label="Meeting key")
    session_key = forms.IntegerField(required=False, label="Session key (opsional)")

    class Meta:
        model = Car
        fields = [
            "meeting_key",
            "session_key",
            "date",
            "driver_number",
            "speed",
            "throttle",
            "brake",
            "n_gear",
            "rpm",
            "drs",
        ]

    def clean_meeting_key(self):
        value = self.cleaned_data.get("meeting_key")
        if value in (None, ""):
            return None
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise forms.ValidationError("Meeting key harus berupa angka.")
        if value < 0:
            raise forms.ValidationError("Meeting key harus bernilai positif.")
        meeting_obj, _ = Meeting.objects.get_or_create(meeting_key=value)
        return meeting_obj

    def clean_session_key(self):
        value = self.cleaned_data.get("session_key")
        if value in (None, ""):
            return None
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise forms.ValidationError("Session key harus berupa angka.")
        if value < 0:
            raise forms.ValidationError("Session key harus bernilai positif.")

        meeting_obj = self.cleaned_data.get("meeting_key")
        defaults = {"meeting": meeting_obj} if meeting_obj else {}
        session_obj, _ = Session.objects.get_or_create(
            session_key=value,
            defaults=defaults,
        )
        if meeting_obj and session_obj.meeting_id is None:
            session_obj.meeting = meeting_obj
            session_obj.save(update_fields=["meeting"])
        return session_obj

    def save(self, commit=True):
        car = super().save(commit=False)
        car.is_manual = True
        if car.meeting_key is None and car.session_key and car.session_key.meeting_id:
            car.meeting_key = car.session_key.meeting

        if commit:
            car.save()
        return car

