"""
Global search views.
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.db.models import Q

from apps.permissions.services import PermissionService


@login_required
def global_search(request: HttpRequest) -> HttpResponse:
    """
    Global search across all modules.
    Returns JSON for HTMX requests, full page otherwise.
    """
    query = request.GET.get("q", "").strip()
    organization = getattr(request, "organization", None)

    if not query or len(query) < 2:
        if request.headers.get("HX-Request"):
            return render(request, "search/partials/results_empty.html")
        return render(request, "search/index.html", {"query": query, "results": {}})

    results = {
        "contacts": [],
        "companies": [],
        "opportunities": [],
        "invoices": [],
        "quotes": [],
        "employees": [],
    }

    user = request.user
    permissions = PermissionService.get_user_permissions(user, organization)

    # Search in each module based on permissions
    # Note: These will be implemented when modules are created

    if "crm_view" in permissions and organization:
        # Search contacts
        # results["contacts"] = Contact.objects.filter(
        #     organization=organization
        # ).filter(
        #     Q(first_name__icontains=query) |
        #     Q(last_name__icontains=query) |
        #     Q(email__icontains=query)
        # )[:5]
        pass

    if "invoicing_view" in permissions and organization:
        # Search invoices and quotes
        pass

    if "hr_view" in permissions and organization:
        # Search employees
        pass

    # Count total results
    total_results = sum(len(v) for v in results.values())

    context = {
        "query": query,
        "results": results,
        "total_results": total_results,
    }

    if request.headers.get("HX-Request"):
        return render(request, "search/partials/results.html", context)

    return render(request, "search/index.html", context)


@login_required
def search_suggestions(request: HttpRequest) -> JsonResponse:
    """
    Return search suggestions for autocomplete.
    """
    query = request.GET.get("q", "").strip()

    if not query or len(query) < 2:
        return JsonResponse({"suggestions": []})

    organization = getattr(request, "organization", None)
    suggestions = []

    # Collect suggestions from recent searches or popular items
    # This is a placeholder - implement based on your needs

    return JsonResponse({"suggestions": suggestions[:10]})
