"""
Management command to migrate users to the new OrganizationMembership model.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.core.models import OrganizationMembership


class Command(BaseCommand):
    help = 'Migrate existing users to OrganizationMembership model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        users_with_org = User.objects.filter(organization__isnull=False)
        total = users_with_org.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No users to migrate.'))
            return

        self.stdout.write(f'Found {total} users with organizations to migrate.')

        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for user in users_with_org:
                # Check if membership already exists
                exists = OrganizationMembership.objects.filter(
                    user=user,
                    organization=user.organization
                ).exists()

                if exists:
                    skipped_count += 1
                    if options['verbosity'] >= 2:
                        self.stdout.write(
                            f'  Skipping {user.email} - membership exists'
                        )
                    continue

                # Determine role based on user flags
                if user.is_organization_admin:
                    role = OrganizationMembership.Role.ADMIN
                else:
                    role = OrganizationMembership.Role.MEMBER

                if not dry_run:
                    OrganizationMembership.objects.create(
                        user=user,
                        organization=user.organization,
                        role=role,
                        is_active=True,
                    )

                    # Set active_organization
                    user.active_organization = user.organization
                    user.save(update_fields=['active_organization'])

                created_count += 1
                if options['verbosity'] >= 2:
                    self.stdout.write(
                        f'  Created membership for {user.email} as {role}'
                    )

            if dry_run:
                # Rollback the transaction in dry run mode
                transaction.set_rollback(True)

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Migration complete: {created_count} memberships created, '
                f'{skipped_count} skipped'
            )
        )
