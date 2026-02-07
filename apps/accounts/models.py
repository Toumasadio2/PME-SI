"""
Custom User model with organization support.
"""
import uuid
from typing import Optional

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import Organization, TimeStampedModel


class UserManager(BaseUserManager):
    """Custom user manager using email as username."""

    def create_user(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields
    ) -> "User":
        """Create and return a regular user."""
        if not email:
            raise ValueError("L'adresse email est obligatoire")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        **extra_fields
    ) -> "User":
        """Create and return a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser doit avoir is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Custom user model using email as the unique identifier.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name="Adresse email")

    # Profile
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Nom")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    avatar = models.ImageField(upload_to="avatars/", blank=True, verbose_name="Avatar")
    job_title = models.CharField(max_length=100, blank=True, verbose_name="Fonction")

    # Organization (legacy - kept for backward compatibility)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
        verbose_name="Entreprise",
    )

    # Active organization for multi-tenant support
    active_organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_users",
        verbose_name="Entreprise active",
    )

    # Super admin can access all organizations
    is_super_admin = models.BooleanField(
        default=False,
        verbose_name="Super administrateur",
        help_text="Peut accéder et gérer toutes les entreprises",
    )

    # Status
    is_staff = models.BooleanField(default=False, verbose_name="Staff")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_organization_admin = models.BooleanField(
        default=False,
        verbose_name="Admin entreprise",
        help_text="Peut gérer l'entreprise et ses membres",
    )

    # 2FA
    is_2fa_enabled = models.BooleanField(default=False, verbose_name="2FA activé")
    totp_secret = models.CharField(max_length=32, blank=True)

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Date d'inscription")
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self) -> str:
        """Return the user's first name or email."""
        return self.first_name or self.email.split("@")[0]

    def get_initials(self) -> str:
        """Return user initials for avatar placeholder."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.email[0:2].upper()

    def get_organizations(self):
        """Get all organizations the user has access to."""
        if self.is_super_admin:
            return Organization.objects.filter(is_active=True)
        return Organization.objects.filter(
            memberships__user=self,
            memberships__is_active=True,
            is_active=True,
        )

    def can_access_organization(self, organization: Organization) -> bool:
        """Check if the user can access a specific organization."""
        if self.is_super_admin:
            return True
        return self.memberships.filter(
            organization=organization,
            is_active=True,
        ).exists()

    def get_role_in_organization(self, organization: Organization) -> Optional[str]:
        """Get the user's role in a specific organization."""
        if self.is_super_admin:
            return "super_admin"
        membership = self.memberships.filter(
            organization=organization,
            is_active=True,
        ).first()
        return membership.role if membership else None

    def get_current_organization(self) -> Optional[Organization]:
        """
        Get the current active organization.
        Falls back to legacy organization or first available organization.
        """
        if self.active_organization and self.can_access_organization(self.active_organization):
            return self.active_organization
        if self.organization and self.can_access_organization(self.organization):
            return self.organization
        # Fall back to first available organization
        organizations = self.get_organizations()
        return organizations.first() if organizations.exists() else None

    def switch_organization(self, organization: Organization) -> bool:
        """Switch the user's active organization."""
        if self.can_access_organization(organization):
            self.active_organization = organization
            self.save(update_fields=["active_organization"])
            return True
        return False


class UserInvitation(TimeStampedModel):
    """
    Invitation to join an organization.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        ACCEPTED = "ACCEPTED", "Acceptée"
        EXPIRED = "EXPIRED", "Expirée"
        CANCELLED = "CANCELLED", "Annulée"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(verbose_name="Email invité")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    role = models.CharField(max_length=50, default="user")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Invitation {self.email} -> {self.organization}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def accept(self, user: User) -> None:
        """Accept the invitation."""
        self.status = self.Status.ACCEPTED
        self.accepted_at = timezone.now()
        self.save(update_fields=["status", "accepted_at"])

        user.organization = self.organization
        user.save(update_fields=["organization"])
