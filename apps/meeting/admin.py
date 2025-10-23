from django.contrib import admin

from apps.meeting.models import Meeting


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Meeting)
class MeetingAdmin(ReadOnlyAdmin):
    list_display = ("meeting_key",)
    search_fields = ("meeting_key",)
    ordering = ("meeting_key",)
    readonly_fields = ("meeting_key",)
