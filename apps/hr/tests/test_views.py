"""HR View Tests."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.hr.models import Employee, LeaveRequest

from .factories import (
    DepartmentFactory,
    EmployeeFactory,
    LeaveBalanceFactory,
    LeaveRequestFactory,
    LeaveTypeFactory,
    OrganizationFactory,
    PositionFactory,
)


@pytest.fixture
def org():
    """Create an organization."""
    return OrganizationFactory()


@pytest.fixture
def user(org):
    """Create a user with organization."""
    user = User.objects.create_user(
        email="test@example.com",
        password="testpass123"
    )
    user.organization = org
    user.save()
    return user


@pytest.fixture
def employee(org, user):
    """Create an employee linked to user."""
    emp = EmployeeFactory(organization=org)
    emp.user = user
    emp.save()
    return emp


@pytest.fixture
def authenticated_client(client, user, org):
    """Return authenticated client with organization middleware."""
    client.login(email="test@example.com", password="testpass123")
    # Simulate TenantMiddleware
    client.defaults["HTTP_X_ORGANIZATION"] = str(org.pk)
    return client


@pytest.mark.django_db
class TestEmployeeViews:
    """Tests for Employee views."""

    def test_employee_list_view(self, authenticated_client, org):
        """Test employee list view."""
        EmployeeFactory(organization=org)
        EmployeeFactory(organization=org)

        url = reverse("hr:employee_list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "employees" in response.context

    def test_employee_list_filters(self, authenticated_client, org):
        """Test employee list filtering."""
        dept = DepartmentFactory(organization=org)
        EmployeeFactory(organization=org, department=dept, status=Employee.Status.ACTIVE)
        EmployeeFactory(organization=org, status=Employee.Status.DEPARTED)

        url = reverse("hr:employee_list")

        # Filter by department
        response = authenticated_client.get(url, {"department": str(dept.pk)})
        assert response.status_code == 200
        assert response.context["total_count"] == 1

        # Filter by status
        response = authenticated_client.get(url, {"status": "DEPARTED"})
        assert response.status_code == 200

    def test_employee_detail_view(self, authenticated_client, org):
        """Test employee detail view."""
        employee = EmployeeFactory(organization=org)

        url = reverse("hr:employee_detail", kwargs={"pk": employee.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.context["employee"] == employee

    def test_employee_create_view(self, authenticated_client, org):
        """Test employee creation."""
        dept = DepartmentFactory(organization=org)
        position = PositionFactory(organization=org, department=dept)

        url = reverse("hr:employee_create")
        data = {
            "employee_id": "EMP001",
            "first_name": "Jean",
            "last_name": "Dupont",
            "email": "jean.dupont@example.com",
            "hire_date": date.today().isoformat(),
            "contract_type": Employee.ContractType.CDI,
            "work_hours": "35.0",
            "status": Employee.Status.ACTIVE,
            "department": dept.pk,
            "position": position.pk,
        }

        response = authenticated_client.post(url, data)

        # Should redirect on success
        assert response.status_code in [200, 302]

    def test_employee_update_view(self, authenticated_client, org):
        """Test employee update."""
        employee = EmployeeFactory(organization=org)

        url = reverse("hr:employee_update", kwargs={"pk": employee.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200

    def test_employee_isolation(self, authenticated_client, org):
        """Test that employees from other orgs are not visible."""
        other_org = OrganizationFactory()
        EmployeeFactory(organization=other_org)

        url = reverse("hr:employee_list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        # Should only see employees from own org
        for emp in response.context.get("employees", []):
            assert emp.organization == org


@pytest.mark.django_db
class TestLeaveViews:
    """Tests for Leave views."""

    def test_leave_list_view(self, authenticated_client, employee, org):
        """Test leave list view."""
        LeaveRequestFactory(organization=org, employee=employee)

        url = reverse("hr:leave_list")
        response = authenticated_client.get(url, {"view": "my_requests"})

        assert response.status_code == 200

    def test_leave_request_create(self, authenticated_client, employee, org):
        """Test leave request creation."""
        leave_type = LeaveTypeFactory(organization=org)
        LeaveBalanceFactory(
            organization=org,
            employee=employee,
            leave_type=leave_type,
            acquired=Decimal("25")
        )

        url = reverse("hr:leave_request")
        data = {
            "leave_type": leave_type.pk,
            "start_date": (date.today() + timedelta(days=7)).isoformat(),
            "end_date": (date.today() + timedelta(days=9)).isoformat(),
            "start_half_day": False,
            "end_half_day": False,
            "reason": "Test leave",
        }

        response = authenticated_client.post(url, data)

        # Check redirect or success
        assert response.status_code in [200, 302]

    def test_leave_balance_view(self, authenticated_client, employee, org):
        """Test leave balance view."""
        leave_type = LeaveTypeFactory(organization=org)
        LeaveBalanceFactory(
            organization=org,
            employee=employee,
            leave_type=leave_type
        )

        url = reverse("hr:leave_balance")
        response = authenticated_client.get(url)

        assert response.status_code == 200

    def test_leave_calendar_view(self, authenticated_client, org):
        """Test leave calendar view."""
        url = reverse("hr:leave_calendar")
        response = authenticated_client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestTimesheetViews:
    """Tests for Timesheet views."""

    def test_timesheet_view(self, authenticated_client, employee, org):
        """Test timesheet view."""
        url = reverse("hr:timesheet")
        response = authenticated_client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestDashboardView:
    """Tests for HR Dashboard."""

    def test_dashboard_view(self, authenticated_client, org):
        """Test HR dashboard."""
        EmployeeFactory(organization=org, status=Employee.Status.ACTIVE)
        EmployeeFactory(organization=org, status=Employee.Status.ACTIVE)

        url = reverse("hr:dashboard")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.context["employees_count"] == 2
