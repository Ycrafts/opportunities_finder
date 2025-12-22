from django.contrib import admin

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
    list_display = ("name", "source_type", "enabled", "poll_interval_minutes", "last_run_at")
    list_filter = ("source_type", "enabled")
    search_fields = ("name", "identifier")
