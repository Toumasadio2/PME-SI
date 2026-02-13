"""HR Views."""
import json
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.permissions.decorators import permission_required as perm_required
from apps.permissions.mixins import ModulePermissionMixin, PermissionRequiredMixin

from .forms import (
    AttendanceClockForm,
    DepartmentForm,
    EmployeeForm,
    EmployeeSearchForm,
    HRDocumentUploadForm,
    LeaveApprovalForm,
    LeaveRequestForm,
    LeaveTypeForm,
    PositionForm,
    TimesheetForm,
)
from .models import (
    Attendance,
    Department,
    Employee,
    EmployeeHistory,
    HRDocument,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    Position,
    Timesheet,
)
from .services import HRAnalyticsService, LeaveService, TimesheetService


class HRBaseMixin(LoginRequiredMixin, ModulePermissionMixin):
    """Base mixin for HR views with tenant filtering and module permission."""

    module_required = "hr"

    def get_queryset(self):
        """Filter by current organization."""
        qs = super().get_queryset()
        if hasattr(self.request, "organization") and self.request.organization:
            return qs.filter(organization=self.request.organization)
        return qs.none()

    def form_valid(self, form):
        """Set organization on save."""
        if hasattr(self.request, "organization") and self.request.organization:
            form.instance.organization = self.request.organization
        return super().form_valid(form)


# =============================================================================
# Dashboard
# =============================================================================

class HRDashboardView(HRBaseMixin, TemplateView):
    """HR Dashboard with KPIs and analytics."""

    template_name = "hr/dashboard.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        org = getattr(self.request, "organization", None)

        if not org:
            return context

        today = timezone.now().date()

        # KPIs
        context["employees_count"] = Employee.objects.filter(
            organization=org,
            status=Employee.Status.ACTIVE
        ).count()

        context["pending_leaves"] = LeaveRequest.objects.filter(
            organization=org,
            status=LeaveRequest.Status.PENDING
        ).count()

        # Upcoming birthdays
        context["upcoming_birthdays"] = HRAnalyticsService.get_upcoming_birthdays(org, days=30)[:5]

        # Upcoming contract ends
        context["upcoming_contract_ends"] = HRAnalyticsService.get_upcoming_contract_ends(org, days=30)

        # Recent leaves
        context["recent_leaves"] = LeaveRequest.objects.filter(
            organization=org,
            status__in=[LeaveRequest.Status.APPROVED, LeaveRequest.Status.PENDING]
        ).select_related("employee", "leave_type").order_by("-created_at")[:5]

        # Headcount by department
        headcount = HRAnalyticsService.get_headcount(org)
        context["headcount_by_department"] = json.dumps(headcount["by_department"])
        context["headcount_by_contract"] = json.dumps([
            {"type": k, "count": v} for k, v in headcount["by_contract_type"].items()
        ])

        # Absence rate this month
        first_of_month = today.replace(day=1)
        absence = HRAnalyticsService.get_absence_rate(org, first_of_month, today)
        context["absence_rate"] = absence["absence_rate"]

        # Seniority stats
        context["seniority_stats"] = HRAnalyticsService.get_seniority_stats(org)

        return context


# =============================================================================
# Employees
# =============================================================================

class EmployeeListView(HRBaseMixin, PermissionRequiredMixin, ListView):
    """List all employees."""

    model = Employee
    template_name = "hr/employee_list.html"
    context_object_name = "employees"
    paginate_by = 25
    permission_required = "hr_view"

    def get_queryset(self):
        qs = super().get_queryset().select_related("department", "position", "manager")

        # Search
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(employee_id__icontains=q) |
                Q(email__icontains=q)
            )

        # Department filter
        department = self.request.GET.get("department")
        if department:
            qs = qs.filter(department_id=department)

        # Status filter
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        else:
            # Default to active employees
            qs = qs.filter(status=Employee.Status.ACTIVE)

        # Contract type filter
        contract_type = self.request.GET.get("contract_type")
        if contract_type:
            qs = qs.filter(contract_type=contract_type)

        return qs.order_by("last_name", "first_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = EmployeeSearchForm(
            self.request.GET,
            organization=getattr(self.request, "organization", None)
        )
        context["total_count"] = self.get_queryset().count()
        return context


class EmployeeDetailView(HRBaseMixin, PermissionRequiredMixin, DetailView):
    """Employee detail view with tabs."""

    model = Employee
    template_name = "hr/employee_detail.html"
    context_object_name = "employee"
    permission_required = "hr_view"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "department", "position", "manager", "user"
        ).prefetch_related(
            "documents", "leave_requests", "timesheets", "history"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.object
        year = timezone.now().year

        # Leave balances
        leave_types = LeaveType.objects.filter(
            organization=employee.organization,
            is_active=True
        )
        balances = []
        for lt in leave_types:
            balance = LeaveService.get_employee_balance(employee, lt, year)
            balances.append({
                "leave_type": lt,
                "balance": balance,
            })
        context["leave_balances"] = balances

        # Recent leave requests
        context["recent_leaves"] = employee.leave_requests.select_related(
            "leave_type"
        ).order_by("-created_at")[:10]

        # Recent documents
        context["recent_documents"] = employee.documents.order_by("-created_at")[:10]

        # History
        context["history"] = employee.history.order_by("-event_date")[:20]

        # Direct reports
        context["direct_reports"] = employee.direct_reports.filter(
            status=Employee.Status.ACTIVE
        )

        return context


class EmployeeCreateView(HRBaseMixin, PermissionRequiredMixin, CreateView):
    """Create a new employee."""

    model = Employee
    form_class = EmployeeForm
    template_name = "hr/employee_form.html"
    permission_required = "hr_create"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = getattr(self.request, "organization", None)
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        # Create hire history entry
        EmployeeHistory.objects.create(
            employee=self.object,
            event_type=EmployeeHistory.EventType.HIRE,
            event_date=self.object.hire_date,
            description=f"Embauche en tant que {self.object.position.title if self.object.position else 'N/A'}",
            new_value={
                "department": self.object.department.name if self.object.department else None,
                "position": self.object.position.title if self.object.position else None,
                "contract_type": self.object.contract_type,
            },
            created_by=self.request.user
        )

        messages.success(self.request, "Employé créé avec succès.")
        return response


class EmployeeUpdateView(HRBaseMixin, PermissionRequiredMixin, UpdateView):
    """Update an employee."""

    model = Employee
    form_class = EmployeeForm
    template_name = "hr/employee_form.html"
    permission_required = "hr_edit"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = getattr(self.request, "organization", None)
        return kwargs

    def form_valid(self, form):
        # Track changes for history
        old_obj = Employee.objects.get(pk=self.object.pk)
        changes = {}

        if old_obj.department_id != form.cleaned_data.get("department"):
            changes["department"] = {
                "old": old_obj.department.name if old_obj.department else None,
                "new": form.cleaned_data["department"].name if form.cleaned_data.get("department") else None,
            }

        if old_obj.position_id != form.cleaned_data.get("position"):
            changes["position"] = {
                "old": old_obj.position.title if old_obj.position else None,
                "new": form.cleaned_data["position"].title if form.cleaned_data.get("position") else None,
            }

        if old_obj.salary != form.cleaned_data.get("salary"):
            changes["salary"] = {
                "old": float(old_obj.salary) if old_obj.salary else None,
                "new": float(form.cleaned_data["salary"]) if form.cleaned_data.get("salary") else None,
            }

        response = super().form_valid(form)

        # Create history entries for changes
        for field, change in changes.items():
            if field == "department":
                event_type = EmployeeHistory.EventType.DEPARTMENT_CHANGE
                description = f"Changement de département: {change['old']} → {change['new']}"
            elif field == "position":
                event_type = EmployeeHistory.EventType.POSITION_CHANGE
                description = f"Changement de poste: {change['old']} → {change['new']}"
            elif field == "salary":
                event_type = EmployeeHistory.EventType.SALARY_CHANGE
                description = "Changement de salaire"
            else:
                continue

            EmployeeHistory.objects.create(
                employee=self.object,
                event_type=event_type,
                event_date=timezone.now().date(),
                description=description,
                old_value={"value": change["old"]},
                new_value={"value": change["new"]},
                created_by=self.request.user
            )

        messages.success(self.request, "Employé mis à jour avec succès.")
        return response


class EmployeeDeleteView(HRBaseMixin, PermissionRequiredMixin, DeleteView):
    """Delete an employee."""

    model = Employee
    template_name = "hr/employee_confirm_delete.html"
    success_url = reverse_lazy("hr:employee_list")
    permission_required = "hr_delete"

    def form_valid(self, form):
        messages.success(self.request, "Employé supprimé avec succès.")
        return super().form_valid(form)


class EmployeeListPartialView(EmployeeListView):
    """Partial view for HTMX employee list updates."""

    template_name = "hr/partials/employee_list.html"


# =============================================================================
# Leaves
# =============================================================================

class LeaveRequestListView(HRBaseMixin, PermissionRequiredMixin, ListView):
    """List leave requests."""

    model = LeaveRequest
    template_name = "hr/leave_list.html"
    context_object_name = "leaves"
    paginate_by = 25
    permission_required = "hr_view"

    def get_queryset(self):
        qs = super().get_queryset().select_related("employee", "leave_type", "approved_by")

        # Filter by type: my_requests, team_requests, all
        view_type = self.request.GET.get("view", "my_requests")

        if view_type == "my_requests":
            # Get employee for current user
            if hasattr(self.request.user, "employee_profile") and self.request.user.employee_profile:
                qs = qs.filter(employee=self.request.user.employee_profile)
            else:
                qs = qs.none()
        elif view_type == "team_requests":
            # Get requests from direct reports
            if hasattr(self.request.user, "employee_profile") and self.request.user.employee_profile:
                team_ids = self.request.user.employee_profile.direct_reports.values_list("id", flat=True)
                qs = qs.filter(employee_id__in=team_ids)
            else:
                qs = qs.none()

        # Status filter
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_type"] = self.request.GET.get("view", "my_requests")
        context["statuses"] = LeaveRequest.Status.choices

        # Check if user can approve
        context["can_approve"] = (
            hasattr(self.request.user, "employee_profile") and
            self.request.user.employee_profile and
            self.request.user.employee_profile.direct_reports.exists()
        )

        return context


class LeaveRequestCreateView(HRBaseMixin, PermissionRequiredMixin, CreateView):
    """Create a leave request."""

    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = "hr/leave_request_form.html"
    success_url = reverse_lazy("hr:leave_list")
    permission_required = "hr_create"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = getattr(self.request, "organization", None)

        # Get employee for current user
        if hasattr(self.request.user, "employee_profile"):
            kwargs["employee"] = self.request.user.employee_profile

        return kwargs

    def form_valid(self, form):
        # Set employee
        if hasattr(self.request.user, "employee_profile") and self.request.user.employee_profile:
            form.instance.employee = self.request.user.employee_profile
        else:
            messages.error(self.request, "Vous devez avoir un profil employé pour faire une demande de congé.")
            return self.form_invalid(form)

        # Set status based on leave type
        if form.instance.leave_type.requires_approval:
            form.instance.status = LeaveRequest.Status.PENDING
        else:
            form.instance.status = LeaveRequest.Status.APPROVED
            form.instance.approved_at = timezone.now()

        response = super().form_valid(form)

        # Update balance
        year = form.instance.start_date.year
        balance, _ = LeaveBalance.objects.get_or_create(
            employee=form.instance.employee,
            leave_type=form.instance.leave_type,
            year=year,
            defaults={"organization": form.instance.organization}
        )

        if form.instance.status == LeaveRequest.Status.PENDING:
            balance.pending += form.instance.days_count
        else:
            balance.taken += form.instance.days_count
        balance.save()

        messages.success(self.request, "Demande de congé créée avec succès.")
        return response


class LeaveRequestDetailView(HRBaseMixin, PermissionRequiredMixin, DetailView):
    """Leave request detail view."""

    model = LeaveRequest
    template_name = "hr/leave_detail.html"
    context_object_name = "leave"
    permission_required = "hr_view"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "employee", "leave_type", "approved_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if user can approve this request
        can_approve = False
        if hasattr(self.request.user, "employee_profile") and self.request.user.employee_profile:
            # User is manager of the employee
            can_approve = (
                self.object.employee.manager == self.request.user.employee_profile and
                self.object.status == LeaveRequest.Status.PENDING
            )
        context["can_approve"] = can_approve
        context["approval_form"] = LeaveApprovalForm()

        return context


@perm_required("hr_approve")
def leave_approve(request, pk):
    """Approve a leave request."""
    if request.method != "POST":
        return redirect("hr:leave_list")

    org = getattr(request, "organization", None)
    leave_request = get_object_or_404(LeaveRequest, pk=pk, organization=org)

    if leave_request.status != LeaveRequest.Status.PENDING:
        messages.error(request, "Cette demande ne peut plus être approuvée.")
        return redirect("hr:leave_detail", pk=pk)

    try:
        LeaveService.approve_leave(leave_request, request.user)
        messages.success(request, "Demande approuvée avec succès.")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("hr:leave_detail", pk=pk)


@perm_required("hr_approve")
def leave_reject(request, pk):
    """Reject a leave request."""
    if request.method != "POST":
        return redirect("hr:leave_list")

    org = getattr(request, "organization", None)
    leave_request = get_object_or_404(LeaveRequest, pk=pk, organization=org)

    if leave_request.status != LeaveRequest.Status.PENDING:
        messages.error(request, "Cette demande ne peut plus être refusée.")
        return redirect("hr:leave_detail", pk=pk)

    reason = request.POST.get("rejection_reason", "")

    try:
        LeaveService.reject_leave(leave_request, request.user, reason)
        messages.success(request, "Demande refusée.")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("hr:leave_detail", pk=pk)


class LeaveCalendarView(HRBaseMixin, TemplateView):
    """Leave calendar view."""

    template_name = "hr/leave_calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get leave types for legend
        org = getattr(self.request, "organization", None)
        if org:
            context["leave_types"] = LeaveType.objects.filter(
                organization=org,
                is_active=True
            )

        return context


class LeaveCalendarEventsView(HRBaseMixin, View):
    """API endpoint for leave calendar events."""

    def get(self, request, *args, **kwargs):
        org = getattr(request, "organization", None)
        if not org:
            return JsonResponse([], safe=False)

        start = request.GET.get("start")
        end = request.GET.get("end")

        leaves = LeaveRequest.objects.filter(
            organization=org,
            status__in=[LeaveRequest.Status.APPROVED, LeaveRequest.Status.PENDING]
        ).select_related("employee", "leave_type")

        if start:
            leaves = leaves.filter(end_date__gte=start)
        if end:
            leaves = leaves.filter(start_date__lte=end)

        events = []
        for leave in leaves:
            event = {
                "id": str(leave.id),
                "title": f"{leave.employee.display_name} - {leave.leave_type.name}",
                "start": leave.start_date.isoformat(),
                "end": (leave.end_date + timedelta(days=1)).isoformat(),
                "color": leave.leave_type.color,
                "extendedProps": {
                    "employee": leave.employee.display_name,
                    "leave_type": leave.leave_type.name,
                    "status": leave.get_status_display(),
                    "days": float(leave.days_count),
                }
            }
            if leave.status == LeaveRequest.Status.PENDING:
                event["classNames"] = ["fc-event-pending"]

            events.append(event)

        return JsonResponse(events, safe=False)


class LeaveBalanceView(HRBaseMixin, TemplateView):
    """View leave balances for current user."""

    template_name = "hr/leave_balance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = getattr(self.request, "organization", None)

        if not org:
            return context

        # Get employee for current user
        employee = None
        if hasattr(self.request.user, "employee_profile"):
            employee = self.request.user.employee_profile

        if not employee:
            context["no_employee"] = True
            return context

        year = timezone.now().year
        leave_types = LeaveType.objects.filter(
            organization=org,
            is_active=True
        )

        balances = []
        for lt in leave_types:
            balance = LeaveService.get_employee_balance(employee, lt, year)
            balances.append({
                "leave_type": lt,
                "balance": balance,
            })

        context["employee"] = employee
        context["year"] = year
        context["balances"] = balances

        return context


class LeaveListPartialView(LeaveRequestListView):
    """Partial view for HTMX leave list updates."""

    template_name = "hr/partials/leave_list.html"


# =============================================================================
# Timesheets
# =============================================================================

class TimesheetView(HRBaseMixin, TemplateView):
    """Weekly timesheet entry view."""

    template_name = "hr/timesheet.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get employee for current user
        employee = None
        if hasattr(self.request.user, "employee_profile"):
            employee = self.request.user.employee_profile

        if not employee:
            context["no_employee"] = True
            return context

        # Get week
        week_str = self.request.GET.get("week")
        if week_str:
            try:
                week_start = date.fromisoformat(week_str)
                week_start = week_start - timedelta(days=week_start.weekday())
            except ValueError:
                week_start = date.today() - timedelta(days=date.today().weekday())
        else:
            week_start = date.today() - timedelta(days=date.today().weekday())

        # Get weekly summary
        summary = TimesheetService.get_weekly_summary(employee, week_start)

        context["employee"] = employee
        context["summary"] = summary
        context["week_start"] = week_start
        context["prev_week"] = week_start - timedelta(days=7)
        context["next_week"] = week_start + timedelta(days=7)
        context["form"] = TimesheetForm()

        return context

    def post(self, request, *args, **kwargs):
        """Save timesheet entries."""
        employee = None
        if hasattr(request.user, "employee_profile"):
            employee = request.user.employee_profile

        if not employee:
            messages.error(request, "Vous devez avoir un profil employé.")
            return redirect("hr:timesheet")

        org = getattr(request, "organization", None)

        # Process each day
        for key in request.POST:
            if key.startswith("start_"):
                date_str = key.replace("start_", "")
                try:
                    entry_date = date.fromisoformat(date_str)
                except ValueError:
                    continue

                start_time = request.POST.get(f"start_{date_str}")
                end_time = request.POST.get(f"end_{date_str}")

                if start_time and end_time:
                    from datetime import datetime

                    start = datetime.strptime(start_time, "%H:%M").time()
                    end = datetime.strptime(end_time, "%H:%M").time()

                    # Calculate worked hours
                    worked_hours = TimesheetService.calculate_worked_hours(start, end)

                    timesheet, created = Timesheet.objects.update_or_create(
                        employee=employee,
                        date=entry_date,
                        defaults={
                            "organization": org,
                            "start_time": start,
                            "end_time": end,
                            "worked_hours": worked_hours,
                        }
                    )

        messages.success(request, "Feuille de temps enregistrée.")
        return redirect(request.get_full_path())


class TimesheetSummaryView(HRBaseMixin, TemplateView):
    """Monthly timesheet summary."""

    template_name = "hr/timesheet_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        employee = None
        if hasattr(self.request.user, "employee_profile"):
            employee = self.request.user.employee_profile

        if not employee:
            context["no_employee"] = True
            return context

        # Get month
        year = int(self.request.GET.get("year", timezone.now().year))
        month = int(self.request.GET.get("month", timezone.now().month))

        summary = TimesheetService.get_monthly_summary(employee, year, month)

        context["employee"] = employee
        context["summary"] = summary
        context["year"] = year
        context["month"] = month

        return context


def attendance_clock(request):
    """Clock in/out."""
    if request.method != "POST":
        return redirect("hr:timesheet")

    employee = None
    if hasattr(request.user, "employee_profile"):
        employee = request.user.employee_profile

    if not employee:
        messages.error(request, "Vous devez avoir un profil employé.")
        return redirect("hr:timesheet")

    now = timezone.now()
    today = now.date()

    # Check for existing open attendance
    open_attendance = Attendance.objects.filter(
        employee=employee,
        date=today,
        clock_out__isnull=True
    ).first()

    if open_attendance:
        # Clock out
        open_attendance.clock_out = now
        open_attendance.save()
        messages.success(request, f"Pointage sortie enregistré à {now.strftime('%H:%M')}.")
    else:
        # Clock in
        Attendance.objects.create(
            employee=employee,
            date=today,
            clock_in=now,
            source=Attendance.Source.APP
        )
        messages.success(request, f"Pointage entrée enregistré à {now.strftime('%H:%M')}.")

    # Return to timesheet or HTMX response
    if request.headers.get("HX-Request"):
        return HttpResponse(
            f'<span class="text-green-600">Pointé à {now.strftime("%H:%M")}</span>'
        )

    return redirect("hr:timesheet")


# =============================================================================
# Documents
# =============================================================================

class HRDocumentListView(HRBaseMixin, PermissionRequiredMixin, ListView):
    """List HR documents for an employee."""

    model = HRDocument
    template_name = "hr/document_list.html"
    context_object_name = "documents"
    paginate_by = 25
    permission_required = "hr_view"

    def get_queryset(self):
        qs = super().get_queryset().select_related("employee", "uploaded_by")

        # Filter by employee if specified
        employee_id = self.request.GET.get("employee")
        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        # Filter by type
        doc_type = self.request.GET.get("type")
        if doc_type:
            qs = qs.filter(document_type=doc_type)

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document_types"] = HRDocument.DocumentType.choices
        return context


class HRDocumentUploadView(HRBaseMixin, PermissionRequiredMixin, CreateView):
    """Upload a new HR document."""

    model = HRDocument
    form_class = HRDocumentUploadForm
    template_name = "hr/document_upload.html"
    permission_required = "hr_create"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # If employee is specified in URL, get it
        employee_id = self.request.GET.get("employee")
        if employee_id:
            employee = get_object_or_404(
                Employee,
                pk=employee_id,
                organization=self.request.organization
            )
            context["employee"] = employee

        return context

    def form_valid(self, form):
        # Set employee from URL or form
        employee_id = self.request.GET.get("employee") or self.request.POST.get("employee")
        if employee_id:
            form.instance.employee = get_object_or_404(
                Employee,
                pk=employee_id,
                organization=self.request.organization
            )

        form.instance.uploaded_by = self.request.user
        messages.success(self.request, "Document téléversé avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("hr:employee_detail", kwargs={"pk": self.object.employee.pk})


# =============================================================================
# Departments
# =============================================================================

class DepartmentListView(HRBaseMixin, PermissionRequiredMixin, ListView):
    """List departments."""

    model = Department
    template_name = "hr/department_list.html"
    context_object_name = "departments"
    permission_required = "hr_view"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "parent", "manager"
        ).annotate(
            employees_count=Count("employees", filter=Q(employees__status=Employee.Status.ACTIVE))
        )


class DepartmentCreateView(HRBaseMixin, PermissionRequiredMixin, CreateView):
    """Create a department."""

    model = Department
    form_class = DepartmentForm
    template_name = "hr/department_form.html"
    success_url = reverse_lazy("hr:department_list")
    permission_required = "hr_create"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = getattr(self.request, "organization", None)
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Département créé avec succès.")
        return super().form_valid(form)


class DepartmentUpdateView(HRBaseMixin, PermissionRequiredMixin, UpdateView):
    """Update a department."""

    model = Department
    form_class = DepartmentForm
    template_name = "hr/department_form.html"
    success_url = reverse_lazy("hr:department_list")
    permission_required = "hr_edit"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = getattr(self.request, "organization", None)
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Département mis à jour avec succès.")
        return super().form_valid(form)


# =============================================================================
# Leave Types
# =============================================================================

class LeaveTypeListView(HRBaseMixin, PermissionRequiredMixin, ListView):
    """List leave types."""

    model = LeaveType
    template_name = "hr/leave_type_list.html"
    context_object_name = "leave_types"
    permission_required = "hr_view"


class LeaveTypeCreateView(HRBaseMixin, PermissionRequiredMixin, CreateView):
    """Create a leave type."""

    model = LeaveType
    form_class = LeaveTypeForm
    template_name = "hr/leave_type_form.html"
    success_url = reverse_lazy("hr:leave_type_list")
    permission_required = "hr_create"

    def form_valid(self, form):
        messages.success(self.request, "Type de congé créé avec succès.")
        return super().form_valid(form)


class LeaveTypeUpdateView(HRBaseMixin, PermissionRequiredMixin, UpdateView):
    """Update a leave type."""

    model = LeaveType
    form_class = LeaveTypeForm
    template_name = "hr/leave_type_form.html"
    success_url = reverse_lazy("hr:leave_type_list")
    permission_required = "hr_edit"

    def form_valid(self, form):
        messages.success(self.request, "Type de congé mis à jour avec succès.")
        return super().form_valid(form)


# =============================================================================
# HTMX Helpers
# =============================================================================

def calculate_leave_days(request):
    """HTMX endpoint to calculate leave days."""
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    start_half = request.GET.get("start_half_day") == "on"
    end_half = request.GET.get("end_half_day") == "on"

    if not start_date or not end_date:
        return HttpResponse("0 jour(s)")

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        days = LeaveService.calculate_working_days(start, end, start_half, end_half)
        return HttpResponse(f"{days} jour(s)")
    except (ValueError, TypeError):
        return HttpResponse("0 jour(s)")
