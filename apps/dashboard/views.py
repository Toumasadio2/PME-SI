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


@login_required
def index(request: HttpRequest) -> HttpResponse:
    """Main dashboard view."""
    user = request.user
    organization = getattr(request, "organization", None)

    # Get user permissions for showing/hiding widgets
    permissions = PermissionService.get_user_permissions(user, organization)

    context = {
        "user": user,
        "organization": organization,
        "permissions": permissions,
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
