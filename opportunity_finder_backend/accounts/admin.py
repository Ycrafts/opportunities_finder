from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import SubscriptionLevel, SubscriptionUpgradeRequest, User, UserRole


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "role", "subscription_level", "is_staff", "is_active")
    search_fields = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Role & Permissions"),
            {
                "fields": (
                    "role",
                    "subscription_level",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "subscription_level",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


@admin.register(SubscriptionUpgradeRequest)
class SubscriptionUpgradeRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "payment_method", "created_at", "reviewed_at")
    list_filter = ("status", "payment_method")
    search_fields = ("user__email",)
    readonly_fields = ("created_at", "updated_at", "reviewed_at")
    actions = ("approve_requests", "reject_requests")

    def approve_requests(self, request, queryset):
        for upgrade_request in queryset:
            upgrade_request.status = SubscriptionUpgradeRequest.Status.APPROVED
            upgrade_request.reviewed_by = request.user
            upgrade_request.reviewed_at = timezone.now()
            upgrade_request.save(update_fields=["status", "reviewed_by", "reviewed_at"])
            upgrade_request.user.subscription_level = SubscriptionLevel.PREMIUM
            upgrade_request.user.save(update_fields=["subscription_level"])

    def reject_requests(self, request, queryset):
        queryset.update(
            status=SubscriptionUpgradeRequest.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )

    approve_requests.short_description = "Approve selected upgrade requests"
    reject_requests.short_description = "Reject selected upgrade requests"
