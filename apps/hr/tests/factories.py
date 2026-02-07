"""HR Test Factories."""
import factory
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from apps.core.models import Organization
from apps.hr.models import (
    Attendance,
    Department,
    Employee,
    EmployeeHistory,
    HRDocument,
    HRDocumentTemplate,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    Position,
    Timesheet,
)


class OrganizationFactory(factory.django.DjangoModelFactory):
    """Factory for Organization model."""

    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Organization {n}")
    slug = factory.Sequence(lambda n: f"org-{n}")


class DepartmentFactory(factory.django.DjangoModelFactory):
    """Factory for Department model."""

    class Meta:
        model = Department

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f"Department {n}")
    code = factory.Sequence(lambda n: f"DEPT{n:03d}")


class PositionFactory(factory.django.DjangoModelFactory):
    """Factory for Position model."""

    class Meta:
        model = Position

    organization = factory.SubFactory(OrganizationFactory)
    title = factory.Sequence(lambda n: f"Position {n}")
    department = factory.SubFactory(DepartmentFactory, organization=factory.SelfAttribute("..organization"))


class EmployeeFactory(factory.django.DjangoModelFactory):
    """Factory for Employee model."""

    class Meta:
        model = Employee

    organization = factory.SubFactory(OrganizationFactory)
    employee_id = factory.Sequence(lambda n: f"EMP{n:05d}")
    first_name = factory.Faker("first_name", locale="fr_FR")
    last_name = factory.Faker("last_name", locale="fr_FR")
    email = factory.LazyAttribute(lambda o: f"{o.first_name.lower()}.{o.last_name.lower()}@example.com")
    hire_date = factory.LazyFunction(lambda: date.today() - timedelta(days=365))
    contract_type = Employee.ContractType.CDI
    work_hours = Decimal("35.0")
    status = Employee.Status.ACTIVE

    @factory.lazy_attribute
    def department(self):
        return DepartmentFactory(organization=self.organization)

    @factory.lazy_attribute
    def position(self):
        return PositionFactory(organization=self.organization, department=self.department)


class LeaveTypeFactory(factory.django.DjangoModelFactory):
    """Factory for LeaveType model."""

    class Meta:
        model = LeaveType

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f"Leave Type {n}")
    code = factory.Sequence(lambda n: f"LT{n:02d}")
    is_paid = True
    requires_approval = True
    max_days_per_year = 25
    accrual_rate = Decimal("2.08")
    color = "#3B82F6"
    is_active = True


class LeaveBalanceFactory(factory.django.DjangoModelFactory):
    """Factory for LeaveBalance model."""

    class Meta:
        model = LeaveBalance

    organization = factory.SubFactory(OrganizationFactory)
    employee = factory.SubFactory(EmployeeFactory, organization=factory.SelfAttribute("..organization"))
    leave_type = factory.SubFactory(LeaveTypeFactory, organization=factory.SelfAttribute("..organization"))
    year = factory.LazyFunction(lambda: timezone.now().year)
    acquired = Decimal("25.0")
    taken = Decimal("0")
    pending = Decimal("0")
    carried_over = Decimal("0")


class LeaveRequestFactory(factory.django.DjangoModelFactory):
    """Factory for LeaveRequest model."""

    class Meta:
        model = LeaveRequest

    organization = factory.SubFactory(OrganizationFactory)
    employee = factory.SubFactory(EmployeeFactory, organization=factory.SelfAttribute("..organization"))
    leave_type = factory.SubFactory(LeaveTypeFactory, organization=factory.SelfAttribute("..organization"))
    start_date = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    end_date = factory.LazyFunction(lambda: date.today() + timedelta(days=9))
    start_half_day = False
    end_half_day = False
    days_count = Decimal("3")
    status = LeaveRequest.Status.PENDING


class TimesheetFactory(factory.django.DjangoModelFactory):
    """Factory for Timesheet model."""

    class Meta:
        model = Timesheet

    organization = factory.SubFactory(OrganizationFactory)
    employee = factory.SubFactory(EmployeeFactory, organization=factory.SelfAttribute("..organization"))
    date = factory.LazyFunction(date.today)
    start_time = factory.LazyFunction(lambda: timezone.datetime(2024, 1, 1, 9, 0).time())
    end_time = factory.LazyFunction(lambda: timezone.datetime(2024, 1, 1, 17, 30).time())
    worked_hours = Decimal("7.5")
    overtime_hours = Decimal("0")
    status = Timesheet.Status.DRAFT


class AttendanceFactory(factory.django.DjangoModelFactory):
    """Factory for Attendance model."""

    class Meta:
        model = Attendance

    employee = factory.SubFactory(EmployeeFactory)
    date = factory.LazyFunction(date.today)
    clock_in = factory.LazyFunction(timezone.now)
    source = Attendance.Source.MANUAL


class HRDocumentFactory(factory.django.DjangoModelFactory):
    """Factory for HRDocument model."""

    class Meta:
        model = HRDocument

    organization = factory.SubFactory(OrganizationFactory)
    employee = factory.SubFactory(EmployeeFactory, organization=factory.SelfAttribute("..organization"))
    document_type = HRDocument.DocumentType.CONTRACT
    title = factory.Sequence(lambda n: f"Document {n}")
    file = factory.django.FileField(filename="test_document.pdf")
    is_confidential = False


class EmployeeHistoryFactory(factory.django.DjangoModelFactory):
    """Factory for EmployeeHistory model."""

    class Meta:
        model = EmployeeHistory

    employee = factory.SubFactory(EmployeeFactory)
    event_type = EmployeeHistory.EventType.HIRE
    event_date = factory.LazyFunction(date.today)
    description = "Test event"


class HRDocumentTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for HRDocumentTemplate model."""

    class Meta:
        model = HRDocumentTemplate

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f"Template {n}")
    document_type = HRDocumentTemplate.TemplateType.ATTESTATION
    content = "<p>Dear {{ employee.first_name }},</p>"
    variables = ["employee.first_name", "employee.last_name"]
    is_active = True
