from django import forms
from django.core.exceptions import ValidationError
from .models import Team

class TeamForm(forms.ModelForm):
    # ============ Custom Fields ============
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
    team_colour_secondary = forms.CharField(
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

    # ============ Meta ============
    class Meta:
        model = Team
        fields = [
            "team_name", "short_code",
            "team_logo_url", "team_colour", "team_colour_secondary",
            "country", "base", "founded_year", "is_active",
            "website", "wiki_url",
            "team_description", "engines",
            "constructors_championships", "drivers_championships",
            "race_victories", "podiums", "points",
        ]
        error_messages = {
            "team_name": {
                "required": "Team name can’t be empty.",
                "unique": "A team named “%(value)s” already exists.",
                "max_length": "Team name is too long.",
            },
            "short_code": {
                "max_length": "Short code must not exceed 8 characters.",
            },
            "founded_year": {
                "invalid": "Please enter a valid year.",
            },
        }
        widgets = {
            "team_logo_url": forms.Textarea(attrs={"rows": 2}),
            "team_description": forms.Textarea(attrs={"rows": 20}),
            "engines": forms.Textarea(attrs={"rows": 2}),
        }

    # ============ Clean Methods ============
    def clean_team_name(self):
        name = (self.cleaned_data.get("team_name") or "").strip()
        if not name:
            raise ValidationError("Team name can’t be empty.")
        if len(name) > 255:
            raise ValidationError("Team name must not exceed 255 characters.")
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

    def clean_team_colour_secondary(self):
        raw = (self.cleaned_data.get("team_colour_secondary") or "").strip()
        if not raw:
            return ""
        if raw.startswith("#"):
            raw = raw[1:]
        if len(raw) != 6:
            raise ValidationError("Secondary colour must be exactly 6 hex digits, e.g., 00A19A.")
        for ch in raw:
            if ch not in "0123456789ABCDEFabcdef":
                raise ValidationError("Secondary colour must contain only 0–9 or A–F characters.")
        return raw.upper()

    def clean_founded_year(self):
        year = self.cleaned_data.get("founded_year")
        if year and (year < 1800 or year > 2100):
            raise ValidationError("Founded year must be between 1800 and 2100.")
        return year

    def clean_short_code(self):
        code = (self.cleaned_data.get("short_code") or "").strip().upper()
        if len(code) > 8:
            raise ValidationError("Short code must not exceed 8 characters.")
        return code

    def clean(self):
        cleaned = super().clean()
        logo = cleaned.get("team_logo_url")
        website = cleaned.get("website")
        wiki = cleaned.get("wiki_url")

        if logo and not (logo.startswith("http://") or logo.startswith("https://")):
            self.add_error("team_logo_url", "Logo URL must start with http:// or https://")

        for field in ("website", "wiki_url"):
            value = cleaned.get(field)
            if value and not (value.startswith("http://") or value.startswith("https://")):
                self.add_error(field, "URL must start with http:// or https://")

        return cleaned