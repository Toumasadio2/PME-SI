"""
Account admin configuration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserInvitation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "organization", "is_active", "is_staff"]
    list_filter = ["is_active", "is_staff", "is_superuser", "organization", "is_2fa_enabled"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations personnelles", {
            "fields": ("first_name", "last_name", "phone", "avatar", "job_title")
        }),
        ("Entreprise", {
            "fields": ("organization", "is_organization_admin")
        }),
        ("Sécurité", {
            "fields": ("is_2fa_enabled",)
        }),
        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("Dates importantes", {
            "fields": ("last_login", "date_joined")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "organization", "status", "invited_by", "created_at", "expires_at"]
    list_filter = ["status", "organization", "created_at"]
    search_fields = ["email", "organization__name"]
    readonly_fields = ["token", "created_at", "accepted_at"]
