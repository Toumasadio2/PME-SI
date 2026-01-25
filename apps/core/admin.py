"""
Core admin configuration.
"""
from django.contrib import admin

from .models import Organization, AuditLogEntry


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "email", "is_active", "created_at"]
    list_filter = ["is_active", "country", "created_at"]
    search_fields = ["name", "slug", "email", "siret"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": ("name", "slug", "is_active")
        }),
        ("Informations légales", {
            "fields": ("siret", "address", "city", "postal_code", "country")
        }),
        ("Contact", {
            "fields": ("phone", "email", "website")
        }),
        ("Personnalisation", {
            "fields": ("logo", "primary_color")
        }),
        ("Paramètres", {
            "fields": ("timezone", "currency", "date_format", "trial_ends_at")
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    list_display = ["created_at", "organization", "user", "action", "model_name", "object_repr"]
    list_filter = ["action", "model_name", "created_at"]
    search_fields = ["object_repr", "user__email"]
    readonly_fields = [
        "organization", "user", "action", "model_name", "object_id",
        "object_repr", "changes", "ip_address", "user_agent", "created_at"
    ]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
