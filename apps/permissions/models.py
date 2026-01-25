"""
Role-Based Access Control (RBAC) models.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import Organization, TimeStampedModel


class Permission(models.Model):
    """
    Custom permission definition.
    """

    class Module(models.TextChoices):
        CRM = "crm", "CRM"
        INVOICING = "invoicing", "Facturation"
        SALES = "sales", "Ventes"
        HR = "hr", "RH"
        SETTINGS = "settings", "Paramètres"

    class Action(models.TextChoices):
        VIEW = "view", "Voir"
        CREATE = "create", "Créer"
        EDIT = "edit", "Modifier"
        DELETE = "delete", "Supprimer"
        EXPORT = "export", "Exporter"
        APPROVE = "approve", "Approuver"

    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    module = models.CharField(max_length=50, choices=Module.choices)
    action = models.CharField(max_length=50, choices=Action.choices)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["module", "action"]
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self) -> str:
        return f"{self.module}.{self.action}"

    @classmethod
    def get_codename(cls, module: str, action: str) -> str:
        """Generate codename from module and action."""
        return f"{module}_{action}"


class Role(TimeStampedModel):
    """
    Role with a set of permissions.
    Can be organization-specific or global (system roles).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        related_name="roles",
        blank=True,
    )

    # Organization-specific roles
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="roles",
        help_text="Si null, c'est un rôle système global",
    )

    # System roles
    is_system = models.BooleanField(
        default=False,
        help_text="Rôle système non modifiable",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"
        unique_together = [["name", "organization"]]

    def __str__(self) -> str:
        if self.organization:
            return f"{self.name} ({self.organization.name})"
        return f"{self.name} (Système)"

    def has_permission(self, codename: str) -> bool:
        """Check if role has a specific permission."""
        return self.permissions.filter(codename=codename).exists()


class UserRole(TimeStampedModel):
    """
    Assignment of a role to a user within an organization.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_assignments",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )

    class Meta:
        verbose_name = "Attribution de rôle"
        verbose_name_plural = "Attributions de rôles"
        unique_together = [["user", "role", "organization"]]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.role.name}"
