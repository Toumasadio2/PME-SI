"""
Permission checking services.
"""
from typing import List, Optional

from django.contrib.auth import get_user_model

from apps.core.models import Organization
from .models import Permission, Role, UserRole

User = get_user_model()


class PermissionService:
    """Service for checking user permissions."""

    # Default system roles
    SYSTEM_ROLES = {
        "admin": {
            "name": "Administrateur",
            "description": "Accès complet à toutes les fonctionnalités",
            "permissions": "__all__",
        },
        "manager": {
            "name": "Manager",
            "description": "Gestion des équipes et validation",
            "permissions": [
                "crm_view", "crm_create", "crm_edit", "crm_export",
                "invoicing_view", "invoicing_create", "invoicing_edit", "invoicing_export", "invoicing_approve",
                "sales_view", "sales_create", "sales_edit", "sales_export",
                "hr_view", "hr_approve",
            ],
        },
        "user": {
            "name": "Utilisateur",
            "description": "Accès standard aux fonctionnalités",
            "permissions": [
                "crm_view", "crm_create", "crm_edit",
                "invoicing_view", "invoicing_create", "invoicing_edit",
                "sales_view",
                "hr_view",
            ],
        },
        "viewer": {
            "name": "Lecteur",
            "description": "Accès en lecture seule",
            "permissions": [
                "crm_view",
                "invoicing_view",
                "sales_view",
                "hr_view",
            ],
        },
        "hr_manager": {
            "name": "Responsable RH",
            "description": "Gestion complète des RH",
            "permissions": [
                "hr_view", "hr_create", "hr_edit", "hr_delete", "hr_export", "hr_approve",
            ],
        },
        "sales_manager": {
            "name": "Responsable Commercial",
            "description": "Gestion complète des ventes",
            "permissions": [
                "crm_view", "crm_create", "crm_edit", "crm_delete", "crm_export",
                "invoicing_view", "invoicing_create", "invoicing_edit", "invoicing_export",
                "sales_view", "sales_create", "sales_edit", "sales_delete", "sales_export",
            ],
        },
    }

    @classmethod
    def get_user_permissions(
        cls,
        user: User,
        organization: Optional[Organization] = None
    ) -> List[str]:
        """Get all permission codenames for a user."""
        if user.is_superuser:
            return list(Permission.objects.values_list("codename", flat=True))

        org = organization or user.organization
        if not org:
            return []

        # Organization admin has all permissions
        if user.is_organization_admin:
            return list(Permission.objects.values_list("codename", flat=True))

        # Get permissions from user's roles
        user_roles = UserRole.objects.filter(
            user=user,
            organization=org,
        ).select_related("role").prefetch_related("role__permissions")

        permissions = set()
        for user_role in user_roles:
            for perm in user_role.role.permissions.all():
                permissions.add(perm.codename)

        return list(permissions)

    @classmethod
    def has_permission(
        cls,
        user: User,
        codename: str,
        organization: Optional[Organization] = None
    ) -> bool:
        """Check if user has a specific permission."""
        if user.is_superuser:
            return True

        org = organization or user.organization
        if not org:
            return False

        if user.is_organization_admin:
            return True

        permissions = cls.get_user_permissions(user, org)
        return codename in permissions

    @classmethod
    def has_module_permission(
        cls,
        user: User,
        module: str,
        organization: Optional[Organization] = None
    ) -> bool:
        """Check if user has any permission in a module."""
        if user.is_superuser or user.is_organization_admin:
            return True

        permissions = cls.get_user_permissions(user, organization)
        return any(p.startswith(f"{module}_") for p in permissions)

    @classmethod
    def assign_role(
        cls,
        user: User,
        role: Role,
        organization: Organization
    ) -> UserRole:
        """Assign a role to a user."""
        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            organization=organization,
        )
        return user_role

    @classmethod
    def remove_role(cls, user: User, role: Role, organization: Organization) -> None:
        """Remove a role from a user."""
        UserRole.objects.filter(
            user=user,
            role=role,
            organization=organization,
        ).delete()

    @classmethod
    def create_default_permissions(cls) -> None:
        """Create all default permissions."""
        for module in Permission.Module.values:
            for action in Permission.Action.values:
                codename = Permission.get_codename(module, action)
                Permission.objects.get_or_create(
                    codename=codename,
                    defaults={
                        "name": f"{action.title()} {module}",
                        "module": module,
                        "action": action,
                    }
                )

    @classmethod
    def create_system_roles(cls) -> None:
        """Create default system roles."""
        cls.create_default_permissions()

        all_permissions = list(Permission.objects.all())

        for role_key, role_data in cls.SYSTEM_ROLES.items():
            role, created = Role.objects.get_or_create(
                name=role_data["name"],
                organization=None,
                defaults={
                    "description": role_data["description"],
                    "is_system": True,
                }
            )

            if role_data["permissions"] == "__all__":
                role.permissions.set(all_permissions)
            else:
                perms = Permission.objects.filter(
                    codename__in=role_data["permissions"]
                )
                role.permissions.set(perms)
