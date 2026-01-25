"""
Management command to setup default permissions and roles.
"""
from django.core.management.base import BaseCommand

from apps.permissions.services import PermissionService


class Command(BaseCommand):
    help = "Create default permissions and system roles"

    def handle(self, *args, **options):
        self.stdout.write("Creating default permissions...")
        PermissionService.create_default_permissions()

        self.stdout.write("Creating system roles...")
        PermissionService.create_system_roles()

        self.stdout.write(self.style.SUCCESS("Permissions and roles created successfully!"))
