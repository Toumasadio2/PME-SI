"""
Core models for multi-tenant architecture.
"""
import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from django.db.models import Manager


class TimeStampedModel(models.Model):
    """Abstract model with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(TimeStampedModel):
    """
    Represents a tenant organization.
    All business data is isolated by organization.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)

    # Business info
    siret = models.CharField(max_length=14, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default="France")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Branding
    logo = models.ImageField(upload_to="organizations/logos/", blank=True)
    primary_color = models.CharField(max_length=7, default="#3B82F6")

    # Settings
    timezone = models.CharField(max_length=50, default="Europe/Paris")
    currency = models.CharField(max_length=3, default="EUR")
    date_format = models.CharField(max_length=20, default="%d/%m/%Y")

    # Status
    is_active = models.BooleanField(default=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"

    def __str__(self) -> str:
        return self.name

    @property
    def is_trial_expired(self) -> bool:
        if self.trial_ends_at is None:
            return False
        return timezone.now() > self.trial_ends_at


class TenantMixin(models.Model):
    """
    Abstract mixin for tenant-scoped models.
    All models that should be isolated by organization inherit from this.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        db_index=True,
    )

    class Meta:
        abstract = True


class TenantManager(models.Manager):
    """Manager that automatically filters by organization."""

    def get_queryset(self):
        return super().get_queryset()

    def for_organization(self, organization: Organization):
        """Filter queryset by organization."""
        return self.get_queryset().filter(organization=organization)


class TenantModel(TenantMixin, TimeStampedModel):
    """
    Base model for tenant-scoped data with timestamps.
    """

    objects: "Manager" = TenantManager()

    class Meta:
        abstract = True


class AuditLogEntry(TimeStampedModel):
    """
    Audit log for tracking important changes.
    """

    class Action(models.TextChoices):
        CREATE = "CREATE", "Création"
        UPDATE = "UPDATE", "Modification"
        DELETE = "DELETE", "Suppression"
        LOGIN = "LOGIN", "Connexion"
        LOGOUT = "LOGOUT", "Déconnexion"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journal d'audit"
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["model_name", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} - {self.model_name} - {self.created_at}"
