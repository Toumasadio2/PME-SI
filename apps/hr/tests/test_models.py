"""HR Model Tests."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.hr.models import Employee, LeaveBalance, LeaveRequest, LeaveType

from .factories import (
    DepartmentFactory,
    EmployeeFactory,
    LeaveBalanceFactory,
    LeaveRequestFactory,
    LeaveTypeFactory,
    OrganizationFactory,
    PositionFactory,
    TimesheetFactory,
)


@pytest.mark.django_db
class TestEmployee:
    """Tests for Employee model."""

    def test_create_employee(self):
        """Test creating an employee."""
        employee = EmployeeFactory()
        assert employee.pk is not None
        assert employee.full_name == f"{employee.first_name} {employee.last_name}"

    def test_employee_id_unique_per_org(self):
        """Test that employee_id is unique per organization."""
        org = OrganizationFactory()
        EmployeeFactory(organization=org, employee_id="EMP001")

        # Same org, same employee_id should raise error
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            EmployeeFactory(organization=org, employee_id="EMP001")

    def test_employee_id_unique_different_org(self):
        """Test that same employee_id works for different organizations."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        EmployeeFactory(organization=org1, employee_id="EMP001")
        employee2 = EmployeeFactory(organization=org2, employee_id="EMP001")
        assert employee2.pk is not None

    def test_employee_years_of_service(self):
        """Test years of service calculation."""
        employee = EmployeeFactory(hire_date=date.today() - timedelta(days=730))
        assert employee.years_of_service == 2

    def test_employee_is_active_property(self):
        """Test is_active property."""
        active = EmployeeFactory(status=Employee.Status.ACTIVE)
        departed = EmployeeFactory(status=Employee.Status.DEPARTED)

        assert active.is_active is True
        assert departed.is_active is False

    def test_employee_initials(self):
        """Test get_initials method."""
        employee = EmployeeFactory(first_name="Jean", last_name="Dupont")
        assert employee.get_initials() == "JD"

    def test_employee_age(self):
        """Test age calculation."""
        employee = EmployeeFactory()
        # Set birthday to exactly 30 years ago plus a few days to ensure age is 30
        today = date.today()
        employee.date_of_birth = date(today.year - 30, 1, 1)
        employee.save()
        # Age should be 30 (already had birthday this year since it's Jan 1)
        assert employee.age == 30


@pytest.mark.django_db
class TestDepartment:
    """Tests for Department model."""

    def test_create_department(self):
        """Test creating a department."""
        dept = DepartmentFactory()
        assert dept.pk is not None
        assert str(dept) == dept.name

    def test_department_hierarchy(self):
        """Test department parent-child relationship."""
        org = OrganizationFactory()
        parent = DepartmentFactory(organization=org, name="Parent")
        child = DepartmentFactory(organization=org, name="Child", parent=parent)

        assert child.parent == parent
        assert parent in child.get_hierarchy()

    def test_employees_count(self):
        """Test employees count property."""
        dept = DepartmentFactory()
        EmployeeFactory(organization=dept.organization, department=dept, status=Employee.Status.ACTIVE)
        EmployeeFactory(organization=dept.organization, department=dept, status=Employee.Status.ACTIVE)
        EmployeeFactory(organization=dept.organization, department=dept, status=Employee.Status.DEPARTED)

        assert dept.employees_count == 2


@pytest.mark.django_db
class TestLeaveType:
    """Tests for LeaveType model."""

    def test_create_leave_type(self):
        """Test creating a leave type."""
        leave_type = LeaveTypeFactory(
            name="Congés Payés",
            code="CP",
            accrual_rate=Decimal("2.08")
        )
        assert leave_type.pk is not None
        assert str(leave_type) == "Congés Payés"


@pytest.mark.django_db
class TestLeaveBalance:
    """Tests for LeaveBalance model."""

    def test_create_balance(self):
        """Test creating a leave balance."""
        balance = LeaveBalanceFactory(
            acquired=Decimal("25"),
            taken=Decimal("5"),
            pending=Decimal("3")
        )
        assert balance.pk is not None
        assert balance.available == Decimal("17")  # 25 - 5 - 3

    def test_total_acquired_with_carryover(self):
        """Test total acquired includes carried over."""
        balance = LeaveBalanceFactory(
            acquired=Decimal("25"),
            carried_over=Decimal("5")
        )
        assert balance.total_acquired == Decimal("30")


@pytest.mark.django_db
class TestLeaveRequest:
    """Tests for LeaveRequest model."""

    def test_create_leave_request(self):
        """Test creating a leave request."""
        request = LeaveRequestFactory()
        assert request.pk is not None

    def test_is_pending_property(self):
        """Test is_pending property."""
        pending = LeaveRequestFactory(status=LeaveRequest.Status.PENDING)
        approved = LeaveRequestFactory(status=LeaveRequest.Status.APPROVED)

        assert pending.is_pending is True
        assert approved.is_pending is False

    def test_can_be_cancelled(self):
        """Test can_be_cancelled property."""
        draft = LeaveRequestFactory(status=LeaveRequest.Status.DRAFT)
        pending = LeaveRequestFactory(status=LeaveRequest.Status.PENDING)
        approved = LeaveRequestFactory(status=LeaveRequest.Status.APPROVED)

        assert draft.can_be_cancelled is True
        assert pending.can_be_cancelled is True
        assert approved.can_be_cancelled is False


@pytest.mark.django_db
class TestTimesheet:
    """Tests for Timesheet model."""

    def test_create_timesheet(self):
        """Test creating a timesheet."""
        timesheet = TimesheetFactory()
        assert timesheet.pk is not None

    def test_unique_employee_date(self):
        """Test that employee+date combination is unique."""
        timesheet = TimesheetFactory()

        with pytest.raises(Exception):
            TimesheetFactory(
                employee=timesheet.employee,
                date=timesheet.date
            )
