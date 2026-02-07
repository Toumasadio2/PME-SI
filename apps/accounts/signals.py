"""
Signals for accounts app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import Organization
from .models import User


@receiver(post_save, sender=User)
def create_organization_for_new_user(sender, instance, created, **kwargs):
    """
    Automatically create an organization for new users who don't have one.
    This ensures every user can access the modules.
    """
    if created and not instance.organization and not instance.is_superuser:
        # Create a personal organization for the user
        org_name = instance.full_name or instance.email.split('@')[0]
        organization = Organization.objects.create(
            name=f"Organisation de {org_name}",
            slug=f"org-{instance.id.hex[:8]}",
            is_active=True,
        )

        # Assign the organization to the user and make them admin
        instance.organization = organization
        instance.is_organization_admin = True
        instance.save(update_fields=['organization', 'is_organization_admin'])
