from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import ngettext

from .models import Domain, Location, Opportunity, OpportunityType, RawOpportunity, Source, Specialization


@admin.register(OpportunityType)
class OpportunityTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("name", "opportunity_type")
    list_filter = ("opportunity_type",)
    search_fields = ("name",)


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ("name", "domain")
    list_filter = ("domain",)
    search_fields = ("name", "domain__name")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    list_filter = ("parent",)
    search_fields = ("name",)


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "organization",
        "op_type",
        "domain",
        "specialization",
        "location",
        "work_mode",
        "status",
        "created_at",
    )
    list_filter = ("op_type", "domain", "specialization", "work_mode", "status")
    search_fields = ("title", "organization", "description_en", "source_url")


@admin.register(RawOpportunity)
class RawOpportunityAdmin(admin.ModelAdmin):
    list_display = ("source", "external_id", "status", "ingested_at")
    list_filter = ("source__source_type", "status")
    search_fields = ("source__name", "external_id", "source_url", "raw_text", "text_en")


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = (
        "name", "source_type", "enabled", "health_status", "success_rate_display",
        "total_runs", "last_run_at", "poll_interval_minutes"
    )
    list_filter = ("source_type", "enabled")
    search_fields = ("name", "identifier")
    readonly_fields = (
        "total_runs", "successful_runs", "success_rate_display", "consecutive_failures",
        "items_created_total", "items_updated_total", "last_success_at", "last_error_at",
        "last_error_message", "health_status", "created_at", "updated_at"
    )
    actions = ["enable_sources", "disable_sources", "run_ingestion", "reset_health_metrics"]

    fieldsets = (
        ("Basic Configuration", {
            "fields": ("name", "source_type", "identifier", "enabled", "poll_interval_minutes")
        }),
        ("Health & Performance", {
            "fields": (
                "health_status", "success_rate_display", "total_runs", "successful_runs",
                "consecutive_failures", "items_created_total", "items_updated_total"
            )
        }),
        ("Timestamps", {
            "fields": ("last_run_at", "last_success_at", "last_error_at", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
        ("Error Details", {
            "fields": ("last_error_message",),
            "classes": ("collapse",)
        }),
    )

    def success_rate_display(self, obj):
        """Display success rate with color coding."""
        try:
            rate = float(obj.success_rate or 0)
        except (TypeError, ValueError):
            rate = 0.0
        if rate >= 90:
            color = "green"
        elif rate >= 70:
            color = "orange"
        else:
            color = "red"
        rate_text = f"{rate:.1f}%"
        return format_html(
            '<span style="color: {};">{}</span>',
            color, rate_text
        )
    success_rate_display.short_description = "Success Rate"
    success_rate_display.admin_order_field = "successful_runs"

    def enable_sources(self, request, queryset):
        """Enable selected sources."""
        updated = queryset.update(enabled=True)
        self.message_user(
            request,
            ngettext(
                '%d source was successfully enabled.',
                '%d sources were successfully enabled.',
                updated,
            ) % updated,
        )
    enable_sources.short_description = "Enable selected sources"

    def disable_sources(self, request, queryset):
        """Disable selected sources."""
        updated = queryset.update(enabled=False)
        self.message_user(
            request,
            ngettext(
                '%d source was successfully disabled.',
                '%d sources were successfully disabled.',
                updated,
            ) % updated,
        )
    disable_sources.short_description = "Disable selected sources"

    def run_ingestion(self, request, queryset):
        """Run ingestion for selected sources."""
        from ingestion.services.runner import IngestionRunner

        runner = IngestionRunner()
        total_created = 0
        total_updated = 0
        sources_processed = 0

        for source in queryset.filter(enabled=True):
            try:
                result = runner.run_source(source=source, limit=50)
                total_created += result.created
                total_updated += result.updated
                sources_processed += 1
                self.message_user(
                    request,
                    f"Source '{source.name}': {result.created} created, {result.updated} updated"
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Error running source '{source.name}': {str(e)}",
                    level="ERROR"
                )

        self.message_user(
            request,
            f"Completed: {sources_processed} sources processed, {total_created} created, {total_updated} updated"
        )
    run_ingestion.short_description = "Run ingestion for selected sources"

    def reset_health_metrics(self, request, queryset):
        """Reset health metrics for selected sources."""
        updated = queryset.update(
            last_success_at=None,
            last_error_at=None,
            consecutive_failures=0,
            total_runs=0,
            successful_runs=0,
            items_created_total=0,
            items_updated_total=0,
            last_error_message=""
        )
        self.message_user(
            request,
            ngettext(
                '%d source health metrics were reset.',
                '%d sources health metrics were reset.',
                updated,
            ) % updated,
        )
    reset_health_metrics.short_description = "Reset health metrics for selected sources"
