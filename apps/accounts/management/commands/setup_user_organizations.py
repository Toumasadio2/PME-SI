"""
Management command to create organizations for existing users.
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.core.models import Organization


class Command(BaseCommand):
    help = 'Create organizations for users who do not have one'

    def handle(self, *args, **options):
        users_without_org = User.objects.filter(organization__isnull=True)
        count = users_without_org.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('All users already have organizations.'))
            return

        self.stdout.write(f'Found {count} users without organization.')

        for user in users_without_org:
            org_name = user.full_name or user.email.split('@')[0]
            organization = Organization.objects.create(
                name=f"Organisation de {org_name}",
                slug=f"org-{user.id.hex[:8]}",
                is_active=True,
            )

            user.organization = organization
            user.is_organization_admin = True
            user.save(update_fields=['organization', 'is_organization_admin'])

            self.stdout.write(f'  Created organization for: {user.email}')

        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} organizations.'))
