"""
Dashboard views.
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from apps.permissions.services import PermissionService
from apps.core.models import Organization, OrganizationMembership


@login_required
def index(request: HttpRequest) -> HttpResponse:
    """Main dashboard view."""
    user = request.user

    # Super admin logic
    if getattr(request, 'is_super_admin', False):
        # If super admin is viewing a specific organization, show that org's dashboard
        if getattr(request, 'organization', None):
            return organization_dashboard(request)
        # Otherwise show global dashboard
        return super_admin_dashboard(request)

    # Regular user sees organization dashboard
    return organization_dashboard(request)


def super_admin_dashboard(request: HttpRequest) -> HttpResponse:
    """Global dashboard for super admin."""
    organizations = Organization.objects.filter(is_active=True).order_by('name')

    # Get stats for each organization
    org_stats = []
    for org in organizations:
        # Get admin for this org
        admin_membership = OrganizationMembership.objects.filter(
            organization=org,
            role__in=[OrganizationMembership.Role.OWNER, OrganizationMembership.Role.ADMIN],
            is_active=True
        ).select_related('user').first()

        # Get member count
        member_count = OrganizationMembership.objects.filter(
            organization=org,
            is_active=True
        ).count()

        org_stats.append({
            'organization': org,
            'admin': admin_membership.user if admin_membership else None,
            'member_count': member_count,
        })

    context = {
        'user': request.user,
        'is_super_admin': True,
        'organizations': organizations,
        'org_stats': org_stats,
        'total_organizations': organizations.count(),
    }

    return render(request, "dashboard/super_admin.html", context)


def organization_dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard for regular users (organization-scoped)."""
    user = request.user
    organization = getattr(request, "organization", None)

    # Get user permissions for showing/hiding widgets
    permissions = PermissionService.get_user_permissions(user, organization)

    # Calculate real statistics
    stats = {
        "contacts": 0,
        "revenue": 0,
        "employees": 0,
        "pending_invoices": 0,
    }

    if organization:
        # CRM Stats
        try:
            from apps.crm.models import Contact
            stats["contacts"] = Contact.objects.filter(organization=organization).count()
        except Exception:
            pass

        # HR Stats
        try:
            from apps.hr.models import Employee
            stats["employees"] = Employee.objects.filter(
                organization=organization,
                status=Employee.Status.ACTIVE
            ).count()
        except Exception:
            pass

        # Invoicing Stats
        try:
            from apps.invoicing.models import Invoice
            from decimal import Decimal

            # Pending invoices count
            pending_invoices = Invoice.objects.filter(
                organization=organization,
                status__in=[Invoice.Status.DRAFT, Invoice.Status.SENT, Invoice.Status.OVERDUE]
            )
            stats["pending_invoices"] = pending_invoices.count()

            # Monthly revenue (paid invoices this month)
            current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            paid_this_month = Invoice.objects.filter(
                organization=organization,
                status=Invoice.Status.PAID,
                paid_date__gte=current_month_start
            ).aggregate(total=Sum('total_amount'))
            stats["revenue"] = int(paid_this_month['total'] or 0)
        except Exception:
            pass

    context = {
        "user": user,
        "organization": organization,
        "permissions": permissions,
        "stats": stats,
        "can_view_crm": "crm_view" in permissions,
        "can_view_invoicing": "invoicing_view" in permissions,
        "can_view_sales": "sales_view" in permissions,
        "can_view_hr": "hr_view" in permissions,
        "widgets": [],
    }

    # Build widget list based on permissions
    if context["can_view_crm"]:
        context["widgets"].append({
            "id": "crm_summary",
            "title": "CRM",
            "icon": "users",
            "url": "dashboard:widget_crm",
        })

    if context["can_view_invoicing"]:
        context["widgets"].append({
            "id": "invoicing_summary",
            "title": "Facturation",
            "icon": "file-text",
            "url": "dashboard:widget_invoicing",
        })

    if context["can_view_sales"]:
        context["widgets"].append({
            "id": "sales_summary",
            "title": "Ventes",
            "icon": "trending-up",
            "url": "dashboard:widget_sales",
        })

    if context["can_view_hr"]:
        context["widgets"].append({
            "id": "hr_summary",
            "title": "RH",
            "icon": "briefcase",
            "url": "dashboard:widget_hr",
        })

    return render(request, "dashboard/index.html", context)


@login_required
def widget_crm(request: HttpRequest) -> HttpResponse:
    """CRM widget partial (loaded via HTMX)."""
    organization = getattr(request, "organization", None)

    # Placeholder data - will be replaced with real queries later
    context = {
        "contacts_count": 0,
        "companies_count": 0,
        "opportunities_count": 0,
        "pipeline_value": 0,
        "recent_activities": [],
    }

    return render(request, "dashboard/widgets/crm.html", context)


@login_required
def widget_invoicing(request: HttpRequest) -> HttpResponse:
    """Invoicing widget partial (loaded via HTMX)."""
    organization = getattr(request, "organization", None)

    context = {
        "pending_quotes": 0,
        "pending_invoices": 0,
        "unpaid_amount": 0,
        "monthly_revenue": 0,
        "recent_invoices": [],
    }

    return render(request, "dashboard/widgets/invoicing.html", context)


@login_required
def widget_sales(request: HttpRequest) -> HttpResponse:
    """Sales widget partial (loaded via HTMX)."""
    organization = getattr(request, "organization", None)

    context = {
        "monthly_sales": 0,
        "conversion_rate": 0,
        "average_deal": 0,
        "sales_target_progress": 0,
        "top_products": [],
    }

    return render(request, "dashboard/widgets/sales.html", context)


@login_required
def widget_hr(request: HttpRequest) -> HttpResponse:
    """HR widget partial (loaded via HTMX)."""
    organization = getattr(request, "organization", None)

    context = {
        "employees_count": 0,
        "pending_leaves": 0,
        "birthdays_this_month": [],
        "upcoming_leaves": [],
    }

    if organization:
        from apps.hr.models import Employee, LeaveRequest
        from apps.hr.services import HRAnalyticsService

        # Active employees count
        context["employees_count"] = Employee.objects.filter(
            organization=organization,
            status=Employee.Status.ACTIVE
        ).count()

        # Pending leave requests
        context["pending_leaves"] = LeaveRequest.objects.filter(
            organization=organization,
            status=LeaveRequest.Status.PENDING
        ).count()

        # Upcoming birthdays (next 30 days)
        birthdays = HRAnalyticsService.get_upcoming_birthdays(organization, days=30)
        context["birthdays_this_month"] = [
            f"{b['employee'].first_name} {b['employee'].last_name} - {b['date'].strftime('%d/%m')}"
            for b in birthdays[:5]
        ]

        # Upcoming approved leaves
        context["upcoming_leaves"] = LeaveRequest.objects.filter(
            organization=organization,
            status=LeaveRequest.Status.APPROVED,
            start_date__gte=timezone.now().date()
        ).select_related("employee", "leave_type").order_by("start_date")[:5]

    return render(request, "dashboard/widgets/hr.html", context)


@login_required
def activity_feed(request: HttpRequest) -> HttpResponse:
    """Activity feed partial (loaded via HTMX)."""
    organization = getattr(request, "organization", None)

    # Get recent audit log entries
    from apps.core.models import AuditLogEntry

    activities = []
    if organization:
        activities = AuditLogEntry.objects.filter(
            organization=organization
        ).select_related("user")[:20]

    return render(request, "dashboard/partials/activity_feed.html", {
        "activities": activities,
    })
