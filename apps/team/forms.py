from django import forms
from django.core.exceptions import ValidationError
from .models import Team

class TeamForm(forms.ModelForm):
    team_colour = forms.CharField(
        required=True,
        max_length=7,
        help_text="6-digit hex; with or without # (e.g., #00A19A or 00A19A).",
        widget=forms.TextInput(attrs={
            "placeholder": "#00A19A",
            "pattern": "#?[0-9A-Fa-f]{6}",
            "autocomplete": "off",
        }),
        error_messages={
            "required": "Please provide a colour.",
            "max_length": "Hex colours are 6 characters (optionally prefixed by #).",
        },
    )

    class Meta:
        model = Team
        fields = ["team_name", "team_colour", "team_description"]
        error_messages = {
            "team_name": {
                "required": "Team name can’t be empty.",
                "unique": "A team named “%(value)s” already exists.",
                "max_length": "Team name is too long.",
            }
        }
        widgets = {
            "team_description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_team_name(self):
        name = (self.cleaned_data.get("team_name") or "").strip()
        if not name:
            raise ValidationError("Team name can’t be empty.")
        return name

    def clean_team_colour(self):
        raw = (self.cleaned_data.get("team_colour") or "").strip()
        if raw.startswith("#"):
            raw = raw[1:]

        if len(raw) != 6:
            raise ValidationError("Colour must be exactly 6 hex digits, e.g., 00A19A.")

        for ch in raw:
            if ch not in "0123456789ABCDEFabcdef":
                raise ValidationError("Colour must contain only 0–9 or A–F characters.")

        return raw.upper()

