from django.contrib import admin
from .models import (
    Comparison,
    ComparisonTeam,
    ComparisonCircuit,
    ComparisonDriver,
    ComparisonCar,
)

class ComparisonTeamInline(admin.TabularInline):
    model = ComparisonTeam
    extra = 0
    autocomplete_fields = ("team",)
    ordering = ("order_index",)
    fields = ("team", "order_index")
    raw_id_fields = ()

class ComparisonCircuitInline(admin.TabularInline):
    model = ComparisonCircuit
    extra = 0
    autocomplete_fields = ("circuit",)
    ordering = ("order_index",)
    fields = ("circuit", "order_index")

class ComparisonDriverInline(admin.TabularInline):
    model = ComparisonDriver
    extra = 0
    autocomplete_fields = ("driver",)
    ordering = ("order_index",)
    fields = ("driver", "order_index")

class ComparisonCarInline(admin.TabularInline):
    model = ComparisonCar
    extra = 0
    autocomplete_fields = ("car",)
    ordering = ("order_index",)
    fields = ("car", "order_index")

@admin.register(Comparison)
class ComparisonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "module",
        "owner",
        "is_public",
        "created_at",
        "linked_count",
    )
    list_filter = (
        "module",
        "is_public",
        "created_at",
    )
    search_fields = (
        "id",
        "title",
        "owner__username",
        "owner__email",
    )
    readonly_fields = ("id", "created_at")
    autocomplete_fields = ("owner",)
    ordering = ("-created_at",)
    list_per_page = 50
    fieldsets = (
        ("Comparison", {
            "fields": (
                "id",
                "title",
                "module",
                "owner",
                "is_public",
                "created_at",
            )
        }),
    )

    def get_inlines_for_module(self, module):
        if module == Comparison.MODULE_TEAM:
            return [ComparisonTeamInline]
        if module == Comparison.MODULE_CIRCUIT:
            return [ComparisonCircuitInline]
        if module == Comparison.MODULE_DRIVER:
            return [ComparisonDriverInline]
        if module == Comparison.MODULE_CAR:
            return [ComparisonCarInline]
        return []

    def get_inline_instances(self, request, obj=None):
        base = super().get_inline_instances(request, obj)
        if obj is None:
            return []
        inlines = self.get_inlines_for_module(obj.module)
        return [inline(self.model, self.admin_site) for inline in inlines]

    def linked_count(self, obj):
        if obj.module == Comparison.MODULE_TEAM:
            return obj.team_links.count()
        if obj.module == Comparison.MODULE_CIRCUIT:
            return obj.circuit_links.count()
        if obj.module == Comparison.MODULE_DRIVER:
            return obj.driver_links.count()
        if obj.module == Comparison.MODULE_CAR:
            return obj.car_links.count()
        return 0
    linked_count.short_description = "Items"
