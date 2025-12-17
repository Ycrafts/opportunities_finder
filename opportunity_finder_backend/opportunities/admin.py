from django.contrib import admin

from .models import Domain, JobOpportunity, Location, OpportunityType, Specialization


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


@admin.register(JobOpportunity)
class JobOpportunityAdmin(admin.ModelAdmin):
    list_display = ("title", "op_type", "domain", "specialization", "location", "is_remote", "created_at")
    list_filter = ("op_type", "domain", "specialization", "is_remote")
    search_fields = ("title", "description_en", "source_url")
