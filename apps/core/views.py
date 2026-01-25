"""
Core views.
"""
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """Health check endpoint for monitoring."""
    return JsonResponse({"status": "ok"})


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    """Home page - redirects to dashboard if authenticated."""
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect("dashboard:index")
    return render(request, "core/home.html")


@login_required
def no_organization(request: HttpRequest) -> HttpResponse:
    """Page shown when user has no organization."""
    return render(request, "core/no_organization.html")
