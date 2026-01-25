"""
Notification models.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import Organization, TimeStampedModel


class Notification(TimeStampedModel):
    """
    User notification.
    """

    class Type(models.TextChoices):
        INFO = "info", "Information"
        SUCCESS = "success", "Succès"
        WARNING = "warning", "Avertissement"
        ERROR = "error", "Erreur"
        MENTION = "mention", "Mention"
        APPROVAL = "approval", "Approbation requise"
        REMINDER = "reminder", "Rappel"

    class Category(models.TextChoices):
        SYSTEM = "system", "Système"
        CRM = "crm", "CRM"
        INVOICING = "invoicing", "Facturation"
        SALES = "sales", "Ventes"
        HR = "hr", "RH"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.INFO,
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.SYSTEM,
    )

    # Link to related object
    link = models.CharField(max_length=500, blank=True)
    related_object_type = models.CharField(max_length=100, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Email notification
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
            models.Index(fields=["organization", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} - {self.user.email}"

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class NotificationPreference(TimeStampedModel):
    """
    User notification preferences.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )

    # Email preferences
    email_enabled = models.BooleanField(default=True)
    email_digest = models.BooleanField(
        default=False,
        help_text="Recevoir un résumé quotidien au lieu de notifications individuelles",
    )

    # Category preferences (JSON field for flexibility)
    category_preferences = models.JSONField(
        default=dict,
        help_text="Préférences par catégorie (email, push, in_app)",
    )

    class Meta:
        verbose_name = "Préférence de notification"
        verbose_name_plural = "Préférences de notification"

    def __str__(self) -> str:
        return f"Préférences de {self.user.email}"

    def should_send_email(self, category: str) -> bool:
        """Check if email should be sent for a category."""
        if not self.email_enabled:
            return False
        prefs = self.category_preferences.get(category, {})
        return prefs.get("email", True)
