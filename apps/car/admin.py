from django.contrib import admin

from apps.car.models import Car


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Car)
class CarAdmin(ReadOnlyAdmin):
    list_display = (
        "display_meeting",
        "display_session",
        "driver_number",
        "driver",
        "speed",
        "throttle",
        "brake",
        "is_manual",
        "date",
    )
    list_filter = (
        "is_manual",
        "brake",
        "drs",
        ("meeting_key", admin.RelatedOnlyFieldListFilter),
        ("session_key", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "driver_number",
        "meeting_key__meeting_key",
        "session_key__session_key",
    )
    ordering = ("-date",)
    readonly_fields = (
        "meeting_key",
        "session_key",
        "driver",
        "driver_number",
        "date",
        "speed",
        "throttle",
        "brake",
        "n_gear",
        "rpm",
        "drs",
        "is_manual",
        "created_at",
        "updated_at",
    )

    @admin.display(ordering="meeting_key__meeting_key", description="Meeting")
    def display_meeting(self, obj: Car):
        return obj.meeting_key_value

    @admin.display(ordering="session_key__session_key", description="Session")
    def display_session(self, obj: Car):
        if obj.session_key:
            return f"{obj.session_key.session_key} ({obj.session_key.name or 'Session'})"
        return "-"
