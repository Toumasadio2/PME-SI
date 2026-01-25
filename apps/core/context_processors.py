"""
Context processors for templates.
"""
from django.http import HttpRequest


def tenant_context(request: HttpRequest) -> dict:
    """Add tenant-related context to all templates."""
    context = {
        "current_organization": None,
        "organization_name": "",
        "organization_logo": None,
    }

    if hasattr(request, "organization") and request.organization:
        org = request.organization
        context.update({
            "current_organization": org,
            "organization_name": org.name,
            "organization_logo": org.logo.url if org.logo else None,
            "organization_primary_color": org.primary_color,
        })

    return context
