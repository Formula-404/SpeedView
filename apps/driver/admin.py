from django.contrib import admin
from django.utils.html import format_html

from .models import Driver, DriverEntry, DriverTeam


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields] + list(super().get_readonly_fields(request, obj))
        return super().get_readonly_fields(request, obj)


class ReadOnlyInline(admin.TabularInline):
    can_delete = False
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False


class DriverTeamInline(ReadOnlyInline):
    model = DriverTeam
    fields = ("team", "start_meeting", "end_meeting", "team_colour")
    readonly_fields = fields
    verbose_name = "Team link"
    verbose_name_plural = "Team links"

class DriverEntryInline(ReadOnlyInline):
    model = DriverEntry
    fields = ("session_key", "meeting", "team", "team_colour", "date_start", "date_end")
    readonly_fields = fields
    verbose_name = "Entry"
    verbose_name_plural = "Entries"


# ==== DRIVER ====
@admin.register(Driver)
class DriverAdmin(ReadOnlyAdmin):
    list_display = (
        "driver_number",
        "display_name",
        "country_code",
        "team_names",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "driver_number",
        "first_name",
        "last_name",
        "full_name",
        "broadcast_name",
        "name_acronym",
        "country_code",
    )
    list_filter = ("country_code",)
    ordering = ("driver_number",)
    list_per_page = 50

    fields = (
        "driver_number",
        "first_name",
        "last_name",
        "full_name",
        "broadcast_name",
        "name_acronym",
        "country_code",
        "headshot_url",
        "debut_meeting",
        "biography",
        "teams_preview",
        "created_at",
        "updated_at",
    )
    readonly_fields = fields

    inlines = (DriverTeamInline, DriverEntryInline)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("teams")

    @admin.display(description="Name")
    def display_name(self, obj: Driver):
        return obj.full_name or obj.broadcast_name or obj.name_acronym or f"#{obj.driver_number}"

    @admin.display(description="Teams")
    def team_names(self, obj: Driver):
        names = list(obj.teams.values_list("team_name", flat=True))
        return ", ".join(names) if names else "—"

    @admin.display(description="Teams (preview)")
    def teams_preview(self, obj: Driver):
        names = list(obj.teams.values_list("team_name", flat=True))
        if not names:
            return "—"
        return ", ".join(names)


# ==== DRIVER ENTRY ====
@admin.register(DriverEntry)
class DriverEntryAdmin(ReadOnlyAdmin):
    list_display = ("driver", "session_key", "meeting", "team", "date_start", "date_end")
    list_filter = (
        ("meeting", admin.RelatedOnlyFieldListFilter),
        ("team", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("driver__driver_number", "session_key")
    ordering = ("-date_start",)

    fields = ("driver", "session_key", "meeting", "team", "team_colour", "date_start", "date_end")
    readonly_fields = fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("meeting", "team", "driver")


# ==== DRIVER TEAM LINK ====
@admin.register(DriverTeam)
class DriverTeamAdmin(ReadOnlyAdmin):
    list_display = ("driver", "team", "start_meeting", "end_meeting", "team_colour")
    list_filter = (
        ("team", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("driver__driver_number", "team__team_name")
    ordering = ("driver__driver_number",)

    fields = ("driver", "team", "start_meeting", "end_meeting", "team_colour")
    readonly_fields = fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("driver", "team", "start_meeting", "end_meeting")
