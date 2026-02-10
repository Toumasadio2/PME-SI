"""
Core models for multi-tenant architecture.
"""
import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

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

    class DocumentTemplate(models.TextChoices):
        CLASSIC = "classic", "Classique"
        MODERN = "modern", "Moderne"
        MINIMAL = "minimal", "Minimaliste"
        ELEGANT = "elegant", "Élégant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)

    # Business info
    siret = models.CharField("SIRET", max_length=14, blank=True)
    vat_number = models.CharField("N° TVA", max_length=20, blank=True, help_text="N° TVA intracommunautaire")
    rcs = models.CharField("RCS", max_length=100, blank=True, help_text="Registre du Commerce et des Sociétés")
    capital = models.CharField("Capital", max_length=50, blank=True, help_text="Capital social (ex: 10 000)")
    address = models.TextField("Adresse", blank=True)
    city = models.CharField("Ville", max_length=100, blank=True)
    postal_code = models.CharField("Code postal", max_length=10, blank=True)
    country = models.CharField("Pays", max_length=100, default="France")
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    website = models.URLField("Site web", blank=True)

    # Banking info (for invoices)
    bank_name = models.CharField("Banque", max_length=100, blank=True)
    iban = models.CharField("IBAN", max_length=34, blank=True)
    bic = models.CharField("BIC/SWIFT", max_length=11, blank=True)

    # Branding
    logo = models.ImageField(upload_to="organizations/logos/", blank=True)
    primary_color = models.CharField(max_length=7, default="#3B82F6")
    secondary_color = models.CharField(max_length=7, default="#1E40AF")

    # Document templates
    document_template = models.CharField(
        "Template documents",
        max_length=20,
        choices=DocumentTemplate.choices,
        default=DocumentTemplate.CLASSIC,
        help_text="Style des devis et factures PDF"
    )

    # Settings
    timezone = models.CharField(max_length=50, default="Europe/Paris")
    currency = models.CharField(max_length=3, default="EUR")
    date_format = models.CharField(max_length=20, default="%d/%m/%Y")

    # Status
    is_active = models.BooleanField(default=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate slug from name
            base_slug = slugify(self.name)
            if not base_slug:
                base_slug = "org"
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

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


class OrganizationMembership(TimeStampedModel):
    """
    Represents a user's membership in an organization.
    Allows users to belong to multiple organizations with different roles.
    """

    class Role(models.TextChoices):
        OWNER = "owner", "Propriétaire"
        ADMIN = "admin", "Administrateur"
        MANAGER = "manager", "Manager"
        MEMBER = "member", "Membre"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        "Rôle",
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    is_active = models.BooleanField("Actif", default=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_memberships",
    )
    joined_at = models.DateTimeField("Date d'adhésion", auto_now_add=True)

    class Meta:
        verbose_name = "Adhésion entreprise"
        verbose_name_plural = "Adhésions entreprises"
        unique_together = [["user", "organization"]]
        ordering = ["-joined_at"]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"

    @property
    def is_owner(self) -> bool:
        return self.role == self.Role.OWNER

    @property
    def is_admin(self) -> bool:
        return self.role in [self.Role.OWNER, self.Role.ADMIN]

    @property
    def can_manage_members(self) -> bool:
        return self.role in [self.Role.OWNER, self.Role.ADMIN]

    @property
    def can_manage_organization(self) -> bool:
        return self.role in [self.Role.OWNER, self.Role.ADMIN]


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
