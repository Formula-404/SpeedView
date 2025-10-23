from datetime import timedelta
from django import forms
from django.forms import ModelForm

from apps.car.models import Car
from apps.session.models import Session


def _handle_empty(value):
    if value in (None, "", "None"):
        return None
    return int(value)


class CarForm(ModelForm):
    session_offset_seconds = forms.IntegerField(
        required=False,
        min_value=0,
        label="Offset dari awal session (detik)",
    )
    meeting_key = forms.TypedChoiceField(
        choices=[],
        coerce=_handle_empty,
        empty_value=None,
        required=False,
        label="Meeting key",
    )
    session_key = forms.TypedChoiceField(
        choices=[],
        coerce=_handle_empty,
        empty_value=None,
        required=False,
        label="Session key (opsional)",
    )

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

    def __init__(self, *args, **kwargs):
        meeting_choices_param = kwargs.pop("meeting_choices", None)
        super().__init__(*args, **kwargs)

        meeting_field = self.fields["meeting_key"]
        session_field = self.fields["session_key"]
        offset_field = self.fields["session_offset_seconds"]
        date_field = self.fields["date"]

        meeting_field.widget.attrs.setdefault(
            "class",
            "w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500",
        )
        session_field.widget.attrs.setdefault(
            "class",
            "w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500",
        )
        session_field.widget.attrs.setdefault("data-placeholder", "Pilih session")
        session_field.widget.attrs.setdefault(
            "data-empty-placeholder", "Tidak ada session untuk meeting ini"
        )
        offset_field.widget.attrs.setdefault(
            "class",
            "w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500",
        )
        date_field.widget = forms.HiddenInput()
        date_field.required = False

        meeting_choices = [("", "Pilih meeting")]
        if meeting_choices_param:
            meeting_choices.extend(meeting_choices_param)
        meeting_field.choices = meeting_choices

        selected_meeting_key = None
        if self.is_bound:
            meeting_value = self.data.get(self.add_prefix("meeting_key"))
            try:
                selected_meeting_key = _handle_empty(meeting_value)
            except (TypeError, ValueError):
                selected_meeting_key = None
        else:
            if self.instance.pk and self.instance.meeting_key is not None:
                selected_meeting_key = self.instance.meeting_key
            elif getattr(self.instance, "session_key", None):
                session_obj = Session.objects.filter(
                    session_key=self.instance.session_key
                ).first()
                if session_obj and session_obj.meeting_key is not None:
                    selected_meeting_key = session_obj.meeting_key
                    self.initial.setdefault("meeting_key", selected_meeting_key)

        session_choices = [("", "Pilih session")]
        if selected_meeting_key is not None:
            session_queryset = Session.objects.filter(
                meeting_key=selected_meeting_key
            ).order_by("session_key")
            session_field.widget.attrs.pop("disabled", None)
        else:
            session_queryset = Session.objects.none()
            session_field.widget.attrs.setdefault("disabled", "disabled")

        if self.is_bound:
            session_value = self.data.get(self.add_prefix("session_key"))
        elif self.instance.pk and self.instance.session_key is not None:
            session_value = str(self.instance.session_key)
        else:
            session_value = None

        if selected_meeting_key is None and session_value not in (None, "", "None"):
            try:
                session_key_int = int(session_value)
            except (TypeError, ValueError):
                session_key_int = None
            else:
                session_obj = Session.objects.filter(
                    session_key=session_key_int
                ).first()
                if session_obj:
                    session_queryset = Session.objects.filter(
                        session_key=session_obj.session_key
                    )
                    session_field.widget.attrs.pop("disabled", None)
                    if session_obj.meeting_key is not None and not meeting_field.initial:
                        meeting_field.initial = session_obj.meeting_key

        for session in session_queryset:
            label = session.name or "Session"
            session_choices.append(
                (
                    session.session_key,
                    f"{session.session_key} ({label})" if label else str(session.session_key),
                )
            )

        session_field.choices = session_choices

        self.order_fields(
            [
                "meeting_key",
                "session_key",
                "driver_number",
                "speed",
                "throttle",
                "brake",
                "n_gear",
                "rpm",
                "drs",
                "session_offset_seconds",
                "date",
            ]
        )

        if not self.is_bound:
            offset_field.initial = offset_field.initial or 0
            if self.instance.pk and self.instance.session_key is not None:
                session_obj = Session.objects.filter(
                    session_key=self.instance.session_key
                ).first()
                if session_obj and session_obj.start_time and self.instance.date:
                    delta = self.instance.date - session_obj.start_time
                    offset_field.initial = max(0, int(delta.total_seconds()))
            elif offset_field.initial is None:
                offset_field.initial = 0

    def clean(self):
        cleaned = super().clean()

        session_key = cleaned.get("session_key")
        offset = cleaned.get("session_offset_seconds")

        if session_key in (None, ""):
            self.add_error(
                "session_key",
                "Pilih session supaya tanggal dapat dihitung otomatis.",
            )
            return cleaned

        session_obj = Session.objects.filter(session_key=session_key).first()
        if session_obj is None or session_obj.start_time is None:
            self.add_error(
                "session_key",
                "Session tidak memiliki start time di sistem.",
            )
            return cleaned

        try:
            offset_seconds = int(offset or 0)
        except (TypeError, ValueError):
            self.add_error("session_offset_seconds", "Offset harus berupa angka.")
            return cleaned

        offset_seconds = max(0, offset_seconds)
        cleaned["session_offset_seconds"] = offset_seconds
        cleaned["date"] = session_obj.start_time + timedelta(seconds=offset_seconds)
        return cleaned

    def save(self, commit=True):
        car = super().save(commit=False)
        car.is_manual = True

        if car.meeting_key is None and car.session_key is not None:
            session_obj = Session.objects.filter(
                session_key=car.session_key
            ).first()
            if session_obj and session_obj.meeting_key is not None:
                car.meeting_key = session_obj.meeting_key

        if commit:
            car.save()
        return car

