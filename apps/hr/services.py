"""
HR Business Logic Services.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Dict, List, Optional

from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.template import Context, Template
from django.utils import timezone

if TYPE_CHECKING:
    from apps.core.models import Organization

    from .models import Employee, HRDocumentTemplate, LeaveRequest, LeaveType


class LeaveService:
    """Service for managing leaves and leave balances."""

    # French public holidays (fixed dates, some vary by year)
    FRENCH_HOLIDAYS_FIXED = [
        (1, 1),    # Jour de l'An
        (5, 1),    # Fête du Travail
        (5, 8),    # Victoire 1945
        (7, 14),   # Fête Nationale
        (8, 15),   # Assomption
        (11, 1),   # Toussaint
        (11, 11),  # Armistice
        (12, 25),  # Noël
    ]

    @staticmethod
    def is_french_holiday(check_date: date) -> bool:
        """Check if a date is a French public holiday (fixed dates only)."""
        return (check_date.month, check_date.day) in LeaveService.FRENCH_HOLIDAYS_FIXED

    @staticmethod
    def is_working_day(check_date: date, exclude_holidays: bool = True) -> bool:
        """Check if a date is a working day (not weekend, optionally not holiday)."""
        # Weekend check
        if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Holiday check
        if exclude_holidays and LeaveService.is_french_holiday(check_date):
            return False

        return True

    @staticmethod
    def calculate_working_days(
        start_date: date,
        end_date: date,
        start_half_day: bool = False,
        end_half_day: bool = False,
        exclude_holidays: bool = True
    ) -> Decimal:
        """
        Calculate the number of working days between two dates.

        Args:
            start_date: Start date of the period
            end_date: End date of the period
            start_half_day: If True, start afternoon only (0.5 day)
            end_half_day: If True, end at noon (0.5 day)
            exclude_holidays: If True, exclude French public holidays

        Returns:
            Number of working days as Decimal
        """
        if end_date < start_date:
            return Decimal("0")

        days = Decimal("0")
        current_date = start_date

        while current_date <= end_date:
            if LeaveService.is_working_day(current_date, exclude_holidays):
                if current_date == start_date and start_half_day:
                    days += Decimal("0.5")
                elif current_date == end_date and end_half_day:
                    days += Decimal("0.5")
                else:
                    days += Decimal("1")
            current_date += timedelta(days=1)

        return days

    @staticmethod
    def get_employee_balance(
        employee: "Employee",
        leave_type: "LeaveType",
        year: Optional[int] = None
    ) -> dict:
        """
        Get leave balance for an employee.

        Returns:
            Dict with acquired, taken, pending, available days
        """
        from .models import LeaveBalance

        if year is None:
            year = timezone.now().year

        balance, _ = LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            year=year,
            defaults={
                "organization": employee.organization,
                "acquired": Decimal("0"),
                "taken": Decimal("0"),
                "pending": Decimal("0"),
            }
        )

        return {
            "acquired": balance.acquired,
            "carried_over": balance.carried_over,
            "total": balance.total_acquired,
            "taken": balance.taken,
            "pending": balance.pending,
            "available": balance.available,
        }

    @staticmethod
    @transaction.atomic
    def accrue_leave(
        employee: "Employee",
        leave_type: "LeaveType",
        year: Optional[int] = None,
        days: Optional[Decimal] = None
    ) -> Decimal:
        """
        Accrue leave days for an employee.

        Args:
            employee: The employee
            leave_type: Type of leave to accrue
            year: Year for the balance (defaults to current year)
            days: Number of days to accrue (defaults to leave_type.accrual_rate)

        Returns:
            New total acquired days
        """
        from .models import LeaveBalance

        if year is None:
            year = timezone.now().year

        if days is None:
            days = leave_type.accrual_rate

        balance, _ = LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            year=year,
            defaults={
                "organization": employee.organization,
                "acquired": Decimal("0"),
            }
        )

        balance.acquired += days

        # Check max days per year
        if leave_type.max_days_per_year:
            max_days = Decimal(leave_type.max_days_per_year)
            if balance.acquired > max_days:
                balance.acquired = max_days

        balance.save()
        return balance.acquired

    @staticmethod
    @transaction.atomic
    def request_leave(
        employee: "Employee",
        leave_type: "LeaveType",
        start_date: date,
        end_date: date,
        start_half_day: bool = False,
        end_half_day: bool = False,
        reason: str = "",
        auto_submit: bool = True
    ) -> "LeaveRequest":
        """
        Create a leave request.

        Args:
            employee: The employee requesting leave
            leave_type: Type of leave
            start_date: Start date
            end_date: End date
            start_half_day: Start afternoon only
            end_half_day: End at noon
            reason: Reason for leave
            auto_submit: If True, automatically submit for approval

        Returns:
            The created LeaveRequest
        """
        from .models import LeaveBalance, LeaveRequest

        # Calculate days
        days_count = LeaveService.calculate_working_days(
            start_date, end_date, start_half_day, end_half_day
        )

        # Create request
        status = LeaveRequest.Status.PENDING if auto_submit else LeaveRequest.Status.DRAFT
        if not leave_type.requires_approval:
            status = LeaveRequest.Status.APPROVED

        request = LeaveRequest.objects.create(
            organization=employee.organization,
            employee=employee,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            start_half_day=start_half_day,
            end_half_day=end_half_day,
            days_count=days_count,
            reason=reason,
            status=status,
        )

        # Update pending balance if submitted
        if status == LeaveRequest.Status.PENDING:
            year = start_date.year
            balance, _ = LeaveBalance.objects.get_or_create(
                employee=employee,
                leave_type=leave_type,
                year=year,
                defaults={"organization": employee.organization}
            )
            balance.pending += days_count
            balance.save()

        # If auto-approved, update taken balance
        if status == LeaveRequest.Status.APPROVED:
            year = start_date.year
            balance, _ = LeaveBalance.objects.get_or_create(
                employee=employee,
                leave_type=leave_type,
                year=year,
                defaults={"organization": employee.organization}
            )
            balance.taken += days_count
            balance.save()

        return request

    @staticmethod
    @transaction.atomic
    def approve_leave(
        request: "LeaveRequest",
        approver,
    ) -> "LeaveRequest":
        """Approve a leave request."""
        from .models import LeaveBalance, LeaveRequest

        if request.status != LeaveRequest.Status.PENDING:
            raise ValueError("Can only approve pending requests")

        # Update balance: move from pending to taken
        year = request.start_date.year
        balance = LeaveBalance.objects.filter(
            employee=request.employee,
            leave_type=request.leave_type,
            year=year
        ).first()

        if balance:
            balance.pending -= request.days_count
            balance.taken += request.days_count
            balance.save()

        # Update request
        request.status = LeaveRequest.Status.APPROVED
        request.approved_by = approver
        request.approved_at = timezone.now()
        request.save()

        return request

    @staticmethod
    @transaction.atomic
    def reject_leave(
        request: "LeaveRequest",
        approver,
        reason: str = ""
    ) -> "LeaveRequest":
        """Reject a leave request."""
        from .models import LeaveBalance, LeaveRequest

        if request.status != LeaveRequest.Status.PENDING:
            raise ValueError("Can only reject pending requests")

        # Update balance: remove from pending
        year = request.start_date.year
        balance = LeaveBalance.objects.filter(
            employee=request.employee,
            leave_type=request.leave_type,
            year=year
        ).first()

        if balance:
            balance.pending -= request.days_count
            balance.save()

        # Update request
        request.status = LeaveRequest.Status.REJECTED
        request.approved_by = approver
        request.approved_at = timezone.now()
        request.rejection_reason = reason
        request.save()

        return request

    @staticmethod
    @transaction.atomic
    def cancel_leave(request: "LeaveRequest") -> "LeaveRequest":
        """Cancel a leave request."""
        from .models import LeaveBalance, LeaveRequest

        if not request.can_be_cancelled:
            raise ValueError("This request cannot be cancelled")

        year = request.start_date.year
        balance = LeaveBalance.objects.filter(
            employee=request.employee,
            leave_type=request.leave_type,
            year=year
        ).first()

        if balance:
            if request.status == LeaveRequest.Status.PENDING:
                balance.pending -= request.days_count
            elif request.status == LeaveRequest.Status.APPROVED:
                balance.taken -= request.days_count
            balance.save()

        request.status = LeaveRequest.Status.CANCELLED
        request.save()

        return request

    @staticmethod
    def get_team_calendar(
        manager: "Employee",
        start_date: date,
        end_date: date
    ) -> List[dict]:
        """
        Get leave calendar for a manager's team.

        Returns:
            List of leave events for the team
        """
        from .models import LeaveRequest

        team_members = manager.direct_reports.filter(status="ACTIVE")
        team_ids = list(team_members.values_list("id", flat=True))

        requests = LeaveRequest.objects.filter(
            employee_id__in=team_ids,
            status__in=["PENDING", "APPROVED"],
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related("employee", "leave_type")

        events = []
        for req in requests:
            events.append({
                "id": str(req.id),
                "title": f"{req.employee.display_name} - {req.leave_type.name}",
                "start": req.start_date.isoformat(),
                "end": (req.end_date + timedelta(days=1)).isoformat(),
                "color": req.leave_type.color,
                "employee": req.employee,
                "leave_type": req.leave_type,
                "status": req.status,
            })

        return events


class TimesheetService:
    """Service for managing timesheets and work hours."""

    @staticmethod
    def calculate_worked_hours(
        start_time: datetime.time,
        end_time: datetime.time,
        break_duration: Optional[timedelta] = None
    ) -> Decimal:
        """
        Calculate worked hours from start/end times.

        Args:
            start_time: Clock in time
            end_time: Clock out time
            break_duration: Duration of breaks

        Returns:
            Hours worked as Decimal
        """
        # Create datetime objects for calculation
        base_date = date.today()
        start_dt = datetime.combine(base_date, start_time)
        end_dt = datetime.combine(base_date, end_time)

        # Handle overnight shifts
        if end_dt < start_dt:
            end_dt += timedelta(days=1)

        duration = end_dt - start_dt

        if break_duration:
            duration -= break_duration

        hours = Decimal(duration.total_seconds() / 3600)
        return hours.quantize(Decimal("0.01"))

    @staticmethod
    def calculate_overtime(
        employee: "Employee",
        week_date: date
    ) -> Decimal:
        """
        Calculate overtime hours for a week.

        Args:
            employee: The employee
            week_date: Any date in the week to calculate

        Returns:
            Overtime hours as Decimal
        """
        from .models import Timesheet

        # Get week boundaries
        week_start = week_date - timedelta(days=week_date.weekday())
        week_end = week_start + timedelta(days=6)

        # Get total worked hours for the week
        total = Timesheet.objects.filter(
            employee=employee,
            date__gte=week_start,
            date__lte=week_end
        ).aggregate(total=Sum("worked_hours"))["total"] or Decimal("0")

        # Compare to contractual hours
        contractual = employee.work_hours
        overtime = total - contractual

        return max(Decimal("0"), overtime)

    @staticmethod
    def get_weekly_summary(
        employee: "Employee",
        week_start: date
    ) -> dict:
        """
        Get weekly timesheet summary.

        Returns:
            Dict with daily entries and totals
        """
        from .models import Timesheet

        week_end = week_start + timedelta(days=6)

        entries = Timesheet.objects.filter(
            employee=employee,
            date__gte=week_start,
            date__lte=week_end
        ).order_by("date")

        entries_by_day = {e.date: e for e in entries}

        days = []
        current = week_start
        total_hours = Decimal("0")

        while current <= week_end:
            entry = entries_by_day.get(current)
            days.append({
                "date": current,
                "weekday": current.strftime("%A"),
                "entry": entry,
                "hours": entry.worked_hours if entry else Decimal("0"),
                "is_weekend": current.weekday() >= 5,
            })
            if entry:
                total_hours += entry.worked_hours
            current += timedelta(days=1)

        overtime = total_hours - employee.work_hours
        overtime = max(Decimal("0"), overtime)

        return {
            "week_start": week_start,
            "week_end": week_end,
            "days": days,
            "total_hours": total_hours,
            "contractual_hours": employee.work_hours,
            "overtime": overtime,
        }

    @staticmethod
    def get_monthly_summary(
        employee: "Employee",
        year: int,
        month: int
    ) -> dict:
        """
        Get monthly timesheet summary.

        Returns:
            Dict with statistics for the month
        """
        from calendar import monthrange

        from .models import Timesheet

        _, last_day = monthrange(year, month)
        month_start = date(year, month, 1)
        month_end = date(year, month, last_day)

        entries = Timesheet.objects.filter(
            employee=employee,
            date__gte=month_start,
            date__lte=month_end
        )

        stats = entries.aggregate(
            total_hours=Sum("worked_hours"),
            total_overtime=Sum("overtime_hours"),
            days_count=Count("id")
        )

        return {
            "year": year,
            "month": month,
            "month_start": month_start,
            "month_end": month_end,
            "total_hours": stats["total_hours"] or Decimal("0"),
            "overtime_hours": stats["total_overtime"] or Decimal("0"),
            "days_worked": stats["days_count"] or 0,
        }

    @staticmethod
    def export_for_payroll(
        organization: "Organization",
        year: int,
        month: int
    ) -> List[dict]:
        """
        Export timesheet data for payroll processing.

        Returns:
            List of employee timesheet summaries for CSV export
        """
        from calendar import monthrange

        from .models import Employee, Timesheet

        _, last_day = monthrange(year, month)
        month_start = date(year, month, 1)
        month_end = date(year, month, last_day)

        employees = Employee.objects.filter(
            organization=organization,
            status=Employee.Status.ACTIVE
        )

        data = []
        for emp in employees:
            entries = Timesheet.objects.filter(
                employee=emp,
                date__gte=month_start,
                date__lte=month_end,
                status="VALIDATED"
            )

            stats = entries.aggregate(
                total_hours=Sum("worked_hours"),
                total_overtime=Sum("overtime_hours")
            )

            data.append({
                "employee_id": emp.employee_id,
                "last_name": emp.last_name,
                "first_name": emp.first_name,
                "department": emp.department.name if emp.department else "",
                "contract_type": emp.contract_type,
                "contractual_hours": float(emp.work_hours),
                "worked_hours": float(stats["total_hours"] or 0),
                "overtime_hours": float(stats["total_overtime"] or 0),
            })

        return data


class HRDocumentService:
    """Service for managing HR documents."""

    @staticmethod
    def get_available_variables(employee: "Employee") -> dict:
        """
        Get all available variables for document templates.

        Returns:
            Dict of variable names and their values
        """
        return {
            "employee": {
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "full_name": employee.full_name,
                "employee_id": employee.employee_id,
                "email": employee.email,
                "phone": employee.phone,
                "mobile": employee.mobile,
                "address": employee.address,
                "postal_code": employee.postal_code,
                "city": employee.city,
                "country": employee.country,
                "date_of_birth": employee.date_of_birth,
                "hire_date": employee.hire_date,
                "contract_type": employee.get_contract_type_display(),
                "work_hours": employee.work_hours,
                "salary": employee.salary,
                "social_security_number": employee.social_security_number,
            },
            "department": {
                "name": employee.department.name if employee.department else "",
                "code": employee.department.code if employee.department else "",
            },
            "position": {
                "title": employee.position.title if employee.position else "",
            },
            "organization": {
                "name": employee.organization.name,
                "address": employee.organization.address,
                "city": employee.organization.city,
                "postal_code": employee.organization.postal_code,
                "siret": employee.organization.siret,
            },
            "today": date.today(),
        }

    @staticmethod
    def generate_document(
        template: "HRDocumentTemplate",
        employee: "Employee",
        extra_variables: Optional[dict] = None
    ) -> str:
        """
        Generate a document from a template.

        Args:
            template: The document template
            employee: The employee for the document
            extra_variables: Additional variables to pass to the template

        Returns:
            Rendered HTML content
        """
        variables = HRDocumentService.get_available_variables(employee)

        if extra_variables:
            variables.update(extra_variables)

        django_template = Template(template.content)
        context = Context(variables)

        return django_template.render(context)

    @staticmethod
    def upload_document(
        employee: "Employee",
        file,
        document_type: str,
        title: str,
        user,
        **kwargs
    ):
        """
        Upload a document for an employee.

        Args:
            employee: The employee
            file: The uploaded file
            document_type: Type of document
            title: Document title
            user: User performing the upload
            **kwargs: Additional fields (valid_from, valid_until, is_confidential, notes)

        Returns:
            The created HRDocument
        """
        from .models import HRDocument

        document = HRDocument.objects.create(
            organization=employee.organization,
            employee=employee,
            document_type=document_type,
            title=title,
            file=file,
            uploaded_by=user,
            **kwargs
        )

        return document


class HRAnalyticsService:
    """Service for HR analytics and reporting."""

    @staticmethod
    def get_headcount(
        organization: "Organization",
        as_of_date: Optional[date] = None
    ) -> dict:
        """
        Get headcount statistics.

        Returns:
            Dict with headcount by status, department, contract type
        """
        from .models import Employee

        if as_of_date is None:
            as_of_date = timezone.now().date()

        base_qs = Employee.objects.filter(
            organization=organization,
            hire_date__lte=as_of_date
        ).exclude(
            end_date__lt=as_of_date
        )

        # By status
        by_status = dict(
            base_qs.values("status").annotate(count=Count("id")).values_list("status", "count")
        )

        # By department
        by_department = list(
            base_qs.filter(status=Employee.Status.ACTIVE)
            .values("department__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # By contract type
        by_contract = dict(
            base_qs.filter(status=Employee.Status.ACTIVE)
            .values("contract_type")
            .annotate(count=Count("id"))
            .values_list("contract_type", "count")
        )

        # Total active
        total_active = base_qs.filter(status=Employee.Status.ACTIVE).count()

        return {
            "total_active": total_active,
            "by_status": by_status,
            "by_department": by_department,
            "by_contract_type": by_contract,
            "as_of_date": as_of_date,
        }

    @staticmethod
    def get_turnover_rate(
        organization: "Organization",
        year: int
    ) -> dict:
        """
        Calculate turnover rate for a year.

        Returns:
            Dict with turnover statistics
        """
        from .models import Employee

        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        # Employees at start of year
        start_count = Employee.objects.filter(
            organization=organization,
            hire_date__lt=year_start,
            status__in=[Employee.Status.ACTIVE, Employee.Status.ON_NOTICE]
        ).exclude(end_date__lt=year_start).count()

        # Employees at end of year
        end_count = Employee.objects.filter(
            organization=organization,
            hire_date__lte=year_end,
            status__in=[Employee.Status.ACTIVE, Employee.Status.ON_NOTICE]
        ).exclude(end_date__lt=year_end).count()

        # Average headcount
        avg_headcount = (start_count + end_count) / 2 if (start_count + end_count) > 0 else 1

        # Departures during year
        departures = Employee.objects.filter(
            organization=organization,
            end_date__gte=year_start,
            end_date__lte=year_end
        ).count()

        # New hires during year
        new_hires = Employee.objects.filter(
            organization=organization,
            hire_date__gte=year_start,
            hire_date__lte=year_end
        ).count()

        # Turnover rate
        turnover_rate = (departures / avg_headcount * 100) if avg_headcount > 0 else 0

        return {
            "year": year,
            "start_headcount": start_count,
            "end_headcount": end_count,
            "average_headcount": avg_headcount,
            "new_hires": new_hires,
            "departures": departures,
            "turnover_rate": round(turnover_rate, 1),
        }

    @staticmethod
    def get_absence_rate(
        organization: "Organization",
        start_date: date,
        end_date: date
    ) -> dict:
        """
        Calculate absence rate for a period.

        Returns:
            Dict with absence statistics
        """
        from .models import Employee, LeaveRequest

        # Get active employees
        employees = Employee.objects.filter(
            organization=organization,
            status=Employee.Status.ACTIVE
        )
        employee_count = employees.count()

        if employee_count == 0:
            return {
                "period_start": start_date,
                "period_end": end_date,
                "absence_rate": 0,
                "total_days_absent": 0,
                "employee_count": 0,
            }

        # Calculate working days in period
        working_days = LeaveService.calculate_working_days(start_date, end_date)

        # Total possible days
        total_possible = working_days * employee_count

        # Get approved leaves in period
        leaves = LeaveRequest.objects.filter(
            organization=organization,
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=end_date,
            end_date__gte=start_date
        )

        total_absent_days = Decimal("0")
        for leave in leaves:
            # Calculate overlap with period
            overlap_start = max(leave.start_date, start_date)
            overlap_end = min(leave.end_date, end_date)
            days = LeaveService.calculate_working_days(overlap_start, overlap_end)
            total_absent_days += days

        # Absence rate
        absence_rate = (float(total_absent_days) / float(total_possible) * 100) if total_possible > 0 else 0

        # By leave type
        by_type = (
            leaves.values("leave_type__name")
            .annotate(total=Sum("days_count"))
            .order_by("-total")
        )

        return {
            "period_start": start_date,
            "period_end": end_date,
            "employee_count": employee_count,
            "working_days_in_period": working_days,
            "total_possible_days": total_possible,
            "total_days_absent": total_absent_days,
            "absence_rate": round(absence_rate, 2),
            "by_leave_type": list(by_type),
        }

    @staticmethod
    def get_upcoming_birthdays(
        organization: "Organization",
        days: int = 30
    ) -> list:
        """
        Get employees with birthdays in the next N days.

        Returns:
            List of employees with upcoming birthdays
        """
        from .models import Employee

        today = timezone.now().date()
        employees = Employee.objects.filter(
            organization=organization,
            status=Employee.Status.ACTIVE,
            date_of_birth__isnull=False
        )

        upcoming = []
        for emp in employees:
            # Calculate this year's birthday
            birthday = emp.date_of_birth.replace(year=today.year)
            if birthday < today:
                birthday = birthday.replace(year=today.year + 1)

            days_until = (birthday - today).days
            if 0 <= days_until <= days:
                upcoming.append({
                    "employee": emp,
                    "birthday": birthday,
                    "days_until": days_until,
                    "age": today.year - emp.date_of_birth.year + (1 if birthday.year > today.year else 0)
                })

        return sorted(upcoming, key=lambda x: x["days_until"])

    @staticmethod
    def get_upcoming_contract_ends(
        organization: "Organization",
        days: int = 30
    ) -> list:
        """
        Get employees with contracts ending in the next N days.

        Returns:
            List of employees with upcoming contract ends
        """
        from .models import Employee

        today = timezone.now().date()
        future_date = today + timedelta(days=days)

        employees = Employee.objects.filter(
            organization=organization,
            status=Employee.Status.ACTIVE,
            end_date__isnull=False,
            end_date__gte=today,
            end_date__lte=future_date
        ).order_by("end_date")

        return [
            {
                "employee": emp,
                "end_date": emp.end_date,
                "days_until": (emp.end_date - today).days,
                "contract_type": emp.get_contract_type_display(),
            }
            for emp in employees
        ]

    @staticmethod
    def get_seniority_stats(organization: "Organization") -> dict:
        """
        Get seniority statistics.

        Returns:
            Dict with average seniority and distribution
        """
        from .models import Employee

        today = timezone.now().date()
        employees = Employee.objects.filter(
            organization=organization,
            status=Employee.Status.ACTIVE
        )

        if not employees.exists():
            return {"average_years": 0, "distribution": []}

        # Calculate seniority for each employee
        seniorities = []
        for emp in employees:
            years = (today - emp.hire_date).days / 365
            seniorities.append(years)

        # Average
        avg = sum(seniorities) / len(seniorities) if seniorities else 0

        # Distribution buckets
        buckets = {
            "< 1 an": 0,
            "1-3 ans": 0,
            "3-5 ans": 0,
            "5-10 ans": 0,
            "> 10 ans": 0,
        }

        for years in seniorities:
            if years < 1:
                buckets["< 1 an"] += 1
            elif years < 3:
                buckets["1-3 ans"] += 1
            elif years < 5:
                buckets["3-5 ans"] += 1
            elif years < 10:
                buckets["5-10 ans"] += 1
            else:
                buckets["> 10 ans"] += 1

        return {
            "average_years": round(avg, 1),
            "distribution": [
                {"range": k, "count": v}
                for k, v in buckets.items()
            ],
            "total_employees": len(seniorities),
        }
