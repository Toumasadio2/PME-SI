"""
Initialize system roles and permissions.
"""
from django.core.management.base import BaseCommand

from apps.permissions.models import Permission, Role


class Command(BaseCommand):
    help = "Initialize system roles and permissions"

    def handle(self, *args, **options):
        self.stdout.write("Creating permissions...")

        # Define all permissions
        permissions_data = [
            # CRM
            ("crm_view", "Voir CRM", "crm", "view"),
            ("crm_create", "Créer contacts/entreprises", "crm", "create"),
            ("crm_edit", "Modifier contacts/entreprises", "crm", "edit"),
            ("crm_delete", "Supprimer contacts/entreprises", "crm", "delete"),
            ("crm_export", "Exporter données CRM", "crm", "export"),
            # Invoicing
            ("invoicing_view", "Voir facturation", "invoicing", "view"),
            ("invoicing_create", "Créer devis/factures", "invoicing", "create"),
            ("invoicing_edit", "Modifier devis/factures", "invoicing", "edit"),
            ("invoicing_delete", "Supprimer devis/factures", "invoicing", "delete"),
            ("invoicing_approve", "Valider/envoyer factures", "invoicing", "approve"),
            ("invoicing_export", "Exporter facturation", "invoicing", "export"),
            # Sales
            ("sales_view", "Voir ventes", "sales", "view"),
            ("sales_create", "Créer opportunités", "sales", "create"),
            ("sales_edit", "Modifier opportunités", "sales", "edit"),
            ("sales_delete", "Supprimer opportunités", "sales", "delete"),
            ("sales_export", "Exporter ventes", "sales", "export"),
            # HR
            ("hr_view", "Voir RH", "hr", "view"),
            ("hr_create", "Créer employés/congés", "hr", "create"),
            ("hr_edit", "Modifier employés/congés", "hr", "edit"),
            ("hr_delete", "Supprimer employés/congés", "hr", "delete"),
            ("hr_approve", "Approuver congés", "hr", "approve"),
            ("hr_export", "Exporter données RH", "hr", "export"),
            # Settings
            ("settings_view", "Voir paramètres", "settings", "view"),
            ("settings_edit", "Modifier paramètres", "settings", "edit"),
        ]

        permissions = {}
        for codename, name, module, action in permissions_data:
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "name": name,
                    "module": module,
                    "action": action,
                }
            )
            permissions[codename] = perm
            if created:
                self.stdout.write(f"  Created permission: {codename}")

        self.stdout.write(self.style.SUCCESS(f"  Total: {len(permissions)} permissions"))

        # Define system roles
        roles_data = [
            {
                "name": "Administrateur",
                "description": "Accès complet à tous les modules",
                "permissions": list(permissions.keys()),
            },
            {
                "name": "Manager",
                "description": "Gestion des équipes et validation",
                "permissions": [
                    "crm_view", "crm_create", "crm_edit", "crm_export",
                    "invoicing_view", "invoicing_create", "invoicing_edit", "invoicing_approve", "invoicing_export",
                    "sales_view", "sales_create", "sales_edit", "sales_export",
                    "hr_view", "hr_approve",
                    "settings_view",
                ],
            },
            {
                "name": "Commercial",
                "description": "Gestion des ventes et clients",
                "permissions": [
                    "crm_view", "crm_create", "crm_edit",
                    "invoicing_view", "invoicing_create",
                    "sales_view", "sales_create", "sales_edit",
                ],
            },
            {
                "name": "Comptable",
                "description": "Gestion de la facturation",
                "permissions": [
                    "crm_view",
                    "invoicing_view", "invoicing_create", "invoicing_edit", "invoicing_approve", "invoicing_export",
                    "sales_view", "sales_export",
                ],
            },
            {
                "name": "RH",
                "description": "Gestion des ressources humaines",
                "permissions": [
                    "hr_view", "hr_create", "hr_edit", "hr_delete", "hr_approve", "hr_export",
                ],
            },
            {
                "name": "Utilisateur",
                "description": "Accès en lecture seule",
                "permissions": [
                    "crm_view",
                    "invoicing_view",
                    "sales_view",
                    "hr_view",
                ],
            },
        ]

        self.stdout.write("\nCreating system roles...")
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data["name"],
                organization=None,
                defaults={
                    "description": role_data["description"],
                    "is_system": True,
                }
            )

            # Set permissions
            role_permissions = [permissions[p] for p in role_data["permissions"] if p in permissions]
            role.permissions.set(role_permissions)

            if created:
                self.stdout.write(f"  Created role: {role_data['name']} ({len(role_permissions)} permissions)")
            else:
                self.stdout.write(f"  Updated role: {role_data['name']} ({len(role_permissions)} permissions)")

        self.stdout.write(self.style.SUCCESS("\nSystem roles initialized successfully!"))
