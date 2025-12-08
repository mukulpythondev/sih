from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserOnboardingRequest

# ---------- Jalsetu Admin Branding ----------
admin.site.site_header = "Jalsetu Secure Intelligence Console"
admin.site.site_title = "Jalsetu Admin Panel"
admin.site.index_title = "Jalsetu – RBAC & Data Governance"

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for Jalsetu User with RBAC fields.
    """

    # List page
    list_display = (
        "username",
        "email",
        "role",
        "department",
        "is_active",
        "is_superuser",
        "last_login",
    )
    list_filter = (
        "role",
        "department",
        "is_active",
        "is_superuser",
        "is_staff",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    list_per_page = 30

    # Detail page layout
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {
            "fields": (
                "first_name",
                "last_name",
                "email",
                "department",
            )
        }),
        (_("RBAC & Status"), {
            "fields": (
                "role",
                "access_expires_at",
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    # Add form layout
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "password1",
                "password2",
                "role",
                "department",
                "is_staff",
                "is_superuser",
            ),
        }),
    )


@admin.register(UserOnboardingRequest)
class UserOnboardingRequestAdmin(admin.ModelAdmin):
    """
    Admin panel for appointment/onboarding requests.
    For SUPER_ADMIN / internal view:
    - See who requested which role
    - Track status + decision remark
    """

    list_display = (
        "email",
        "full_name",
        "requested_role",
        "department",
        "status",
        "created_at",
        "decided_at",
        "decided_by",
        "created_user",
    )
    list_filter = (
        "status",
        "requested_role",
        "department",
        "created_at",
    )
    search_fields = ("email", "full_name", "department")
    readonly_fields = (
        "created_at",
        "decided_at",
        "decided_by",
        "created_user",
    )
    ordering = ("-created_at",)
    list_per_page = 30

    # Optional quick actions (no remark granularity, but handy for demo)
    actions = ["approve_selected", "reject_selected"]

    def approve_selected(self, request, queryset):
        updated = 0
        for obj in queryset:
            if obj.status == obj.Status.PENDING:
                obj.status = obj.Status.APPROVED
                obj.decision_remark = obj.decision_remark or "Approved via admin bulk action."
                obj.decided_by = request.user
                obj.save()
                updated += 1
        self.message_user(request, f"{updated} request(s) approved.")

    approve_selected.short_description = "Approve selected onboarding requests (no user creation)"

    def reject_selected(self, request, queryset):
        updated = 0
        for obj in queryset:
            if obj.status == obj.Status.PENDING:
                obj.status = obj.Status.REJECTED
                obj.decision_remark = obj.decision_remark or "Rejected via admin bulk action."
                obj.decided_by = request.user
                obj.save()
                updated += 1
        self.message_user(request, f"{updated} request(s) rejected.")

    reject_selected.short_description = "Reject selected onboarding requests"