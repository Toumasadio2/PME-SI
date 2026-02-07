"""HR Service Tests."""
from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.hr.models import LeaveBalance, LeaveRequest
from apps.hr.services import (
    HRAnalyticsService,
    HRDocumentService,
    LeaveService,
    TimesheetService,
)

from .factories import (
    EmployeeFactory,
    HRDocumentTemplateFactory,
    LeaveBalanceFactory,
    LeaveRequestFactory,
    LeaveTypeFactory,
    OrganizationFactory,
    TimesheetFactory,
)


@pytest.mark.django_db
class TestLeaveService:
    """Tests for LeaveService."""

    def test_is_working_day(self):
        """Test working day detection."""
        monday = date(2024, 1, 8)  # Monday
        saturday = date(2024, 1, 6)  # Saturday

        assert LeaveService.is_working_day(monday) is True
        assert LeaveService.is_working_day(saturday) is False

    def test_is_french_holiday(self):
        """Test French holiday detection."""
        new_year = date(2024, 1, 1)
        regular_day = date(2024, 1, 8)

        assert LeaveService.is_french_holiday(new_year) is True
        assert LeaveService.is_french_holiday(regular_day) is False

    def test_calculate_working_days(self):
        """Test working days calculation."""
        # Monday to Friday (5 working days)
        start = date(2024, 1, 8)  # Monday
        end = date(2024, 1, 12)  # Friday

        days = LeaveService.calculate_working_days(start, end)
        assert days == Decimal("5")

    def test_calculate_working_days_with_weekend(self):
        """Test working days calculation spanning weekend."""
        # Monday to next Monday (6 working days)
        start = date(2024, 1, 8)  # Monday
        end = date(2024, 1, 15)  # Monday

        days = LeaveService.calculate_working_days(start, end)
        assert days == Decimal("6")

    def test_calculate_working_days_half_days(self):
        """Test working days with half days."""
        start = date(2024, 1, 8)  # Monday
        end = date(2024, 1, 10)  # Wednesday

        # Full days: 3
        full = LeaveService.calculate_working_days(start, end)
        assert full == Decimal("3")

        # Start half day: 2.5
        half_start = LeaveService.calculate_working_days(start, end, start_half_day=True)
        assert half_start == Decimal("2.5")

        # End half day: 2.5
        half_end = LeaveService.calculate_working_days(start, end, end_half_day=True)
        assert half_end == Decimal("2.5")

        # Both half days: 2
        both_half = LeaveService.calculate_working_days(start, end, start_half_day=True, end_half_day=True)
        assert both_half == Decimal("2")

    def test_get_employee_balance_creates_if_not_exists(self):
        """Test that get_employee_balance creates balance if needed."""
        employee = EmployeeFactory()
        leave_type = LeaveTypeFactory(organization=employee.organization)
        year = timezone.now().year

        balance = LeaveService.get_employee_balance(employee, leave_type, year)

        assert balance["acquired"] == Decimal("0")
        assert LeaveBalance.objects.filter(
            employee=employee,
            leave_type=leave_type,
            year=year
        ).exists()

    def test_accrue_leave(self):
        """Test leave accrual."""
        employee = EmployeeFactory()
        leave_type = LeaveTypeFactory(
            organization=employee.organization,
            accrual_rate=Decimal("2.5")
        )

        # First accrual
        acquired = LeaveService.accrue_leave(employee, leave_type)
        assert acquired == Decimal("2.5")

        # Second accrual
        acquired = LeaveService.accrue_leave(employee, leave_type)
        assert acquired == Decimal("5.0")

    def test_accrue_leave_respects_max(self):
        """Test that accrual respects max_days_per_year."""
        employee = EmployeeFactory()
        leave_type = LeaveTypeFactory(
            organization=employee.organization,
            accrual_rate=Decimal("10"),
            max_days_per_year=25
        )

        # Accrue more than max
        for _ in range(5):
            LeaveService.accrue_leave(employee, leave_type)

        balance = LeaveBalance.objects.get(
            employee=employee,
            leave_type=leave_type
        )
        assert balance.acquired == Decimal("25")

    def test_request_leave(self):
        """Test leave request creation."""
        employee = EmployeeFactory()
        leave_type = LeaveTypeFactory(
            organization=employee.organization,
            requires_approval=True
        )
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=2)

        request = LeaveService.request_leave(
            employee=employee,
            leave_type=leave_type,
            start_date=start,
            end_date=end
        )

        assert request.pk is not None
        assert request.status == LeaveRequest.Status.PENDING

    def test_approve_leave(self):
        """Test leave approval."""
        request = LeaveRequestFactory(status=LeaveRequest.Status.PENDING)
        LeaveBalanceFactory(
            organization=request.organization,
            employee=request.employee,
            leave_type=request.leave_type,
            pending=request.days_count,
            taken=Decimal("0")
        )

        from apps.accounts.models import User
        approver = User.objects.create(email="approver@test.com")

        approved = LeaveService.approve_leave(request, approver)

        assert approved.status == LeaveRequest.Status.APPROVED
        assert approved.approved_by == approver

        balance = LeaveBalance.objects.get(
            employee=request.employee,
            leave_type=request.leave_type
        )
        assert balance.pending == Decimal("0")
        assert balance.taken == request.days_count

    def test_reject_leave(self):
        """Test leave rejection."""
        request = LeaveRequestFactory(status=LeaveRequest.Status.PENDING)
        LeaveBalanceFactory(
            organization=request.organization,
            employee=request.employee,
            leave_type=request.leave_type,
            pending=request.days_count
        )

        from apps.accounts.models import User
        approver = User.objects.create(email="approver@test.com")

        rejected = LeaveService.reject_leave(request, approver, "Not enough coverage")

        assert rejected.status == LeaveRequest.Status.REJECTED
        assert rejected.rejection_reason == "Not enough coverage"


@pytest.mark.django_db
class TestTimesheetService:
    """Tests for TimesheetService."""

    def test_calculate_worked_hours(self):
        """Test worked hours calculation."""
        hours = TimesheetService.calculate_worked_hours(
            start_time=time(9, 0),
            end_time=time(17, 30),
            break_duration=timedelta(hours=1)
        )
        assert hours == Decimal("7.50")

    def test_get_weekly_summary(self):
        """Test weekly summary."""
        employee = EmployeeFactory()
        week_start = date(2024, 1, 8)  # Monday

        # Create timesheets for some days
        TimesheetFactory(
            organization=employee.organization,
            employee=employee,
            date=week_start,
            worked_hours=Decimal("8")
        )
        TimesheetFactory(
            organization=employee.organization,
            employee=employee,
            date=week_start + timedelta(days=1),
            worked_hours=Decimal("8")
        )

        summary = TimesheetService.get_weekly_summary(employee, week_start)

        assert summary["total_hours"] == Decimal("16")
        assert len(summary["days"]) == 7


@pytest.mark.django_db
class TestHRDocumentService:
    """Tests for HRDocumentService."""

    def test_get_available_variables(self):
        """Test getting available template variables."""
        employee = EmployeeFactory(
            first_name="Jean",
            last_name="Dupont"
        )

        variables = HRDocumentService.get_available_variables(employee)

        assert variables["employee"]["first_name"] == "Jean"
        assert variables["employee"]["last_name"] == "Dupont"
        assert "organization" in variables

    def test_generate_document(self):
        """Test document generation from template."""
        employee = EmployeeFactory(first_name="Jean")
        template = HRDocumentTemplateFactory(
            organization=employee.organization,
            content="<p>Bonjour {{ employee.first_name }}!</p>"
        )

        result = HRDocumentService.generate_document(template, employee)

        assert "Bonjour Jean!" in result


@pytest.mark.django_db
class TestHRAnalyticsService:
    """Tests for HRAnalyticsService."""

    def test_get_headcount(self):
        """Test headcount statistics."""
        org = OrganizationFactory()
        EmployeeFactory(organization=org, status="ACTIVE")
        EmployeeFactory(organization=org, status="ACTIVE")
        EmployeeFactory(organization=org, status="DEPARTED")

        headcount = HRAnalyticsService.get_headcount(org)

        assert headcount["total_active"] == 2

    def test_get_upcoming_birthdays(self):
        """Test upcoming birthdays."""
        org = OrganizationFactory()
        today = timezone.now().date()

        # Employee with birthday in 5 days
        employee = EmployeeFactory(organization=org)
        birthday = today + timedelta(days=5)
        employee.date_of_birth = birthday.replace(year=1990)
        employee.save()

        birthdays = HRAnalyticsService.get_upcoming_birthdays(org, days=30)

        assert len(birthdays) == 1
        assert birthdays[0]["employee"] == employee
