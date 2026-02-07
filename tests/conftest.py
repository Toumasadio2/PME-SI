"""
Pytest configuration and fixtures for PME-SI tests.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.core.models import Organization, OrganizationMembership


User = get_user_model()


@pytest.fixture
def organization(db):
    """Create a test organization."""
    return Organization.objects.create(
        name="Test Organization",
        slug="test-org",
        email="contact@test-org.com",
        siret="12345678901234",
    )


@pytest.fixture
def another_organization(db):
    """Create another test organization for isolation tests."""
    return Organization.objects.create(
        name="Another Organization",
        slug="another-org",
        email="contact@another-org.com",
    )


@pytest.fixture
def user(db, organization):
    """Create a test user with organization membership."""
    user = User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        organization=organization,
        active_organization=organization,
    )
    OrganizationMembership.objects.create(
        user=user,
        organization=organization,
        role=OrganizationMembership.Role.MEMBER,
    )
    return user


@pytest.fixture
def admin_user(db, organization):
    """Create an admin user with organization membership."""
    user = User.objects.create_user(
        email="admin@example.com",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
        organization=organization,
        active_organization=organization,
        is_organization_admin=True,
    )
    OrganizationMembership.objects.create(
        user=user,
        organization=organization,
        role=OrganizationMembership.Role.ADMIN,
    )
    return user


@pytest.fixture
def super_admin(db):
    """Create a super admin user."""
    return User.objects.create_superuser(
        email="superadmin@example.com",
        password="superpass123",
        first_name="Super",
        last_name="Admin",
        is_super_admin=True,
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return an authenticated test client."""
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Return an authenticated admin test client."""
    client.force_login(admin_user)
    return client


# Product fixtures
@pytest.fixture
def product(db, organization):
    """Create a test product."""
    from apps.invoicing.models import Product
    return Product.objects.create(
        organization=organization,
        reference="PROD-001",
        name="Test Product",
        description="A test product",
        product_type="product",
        unit_price="100.00",
        vat_rate="20.00",
    )


@pytest.fixture
def service(db, organization):
    """Create a test service."""
    from apps.invoicing.models import Product
    return Product.objects.create(
        organization=organization,
        reference="SERV-001",
        name="Test Service",
        description="A test service",
        product_type="service",
        unit_price="50.00",
        vat_rate="20.00",
        unit="hour",
    )


# Invoice fixtures
@pytest.fixture
def invoice(db, organization, user):
    """Create a test invoice."""
    from apps.invoicing.models import Invoice
    from django.utils import timezone
    return Invoice.objects.create(
        organization=organization,
        number="FAC-2024-001",
        subject="Test Invoice",
        status="draft",
        issue_date=timezone.now().date(),
        due_date=timezone.now().date() + timezone.timedelta(days=30),
        created_by=user,
    )


@pytest.fixture
def quote(db, organization, user):
    """Create a test quote."""
    from apps.invoicing.models import Quote
    from django.utils import timezone
    return Quote.objects.create(
        organization=organization,
        number="DEV-2024-001",
        subject="Test Quote",
        status="draft",
        issue_date=timezone.now().date(),
        created_by=user,
    )
