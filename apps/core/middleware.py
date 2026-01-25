"""
Tenant middleware for multi-tenant isolation.
"""
import threading
from typing import Optional

from django.http import HttpRequest, HttpResponse, Http404
from django.utils.deprecation import MiddlewareMixin

from .models import Organization

# Thread-local storage for current organization
_thread_locals = threading.local()


def get_current_organization() -> Optional[Organization]:
    """Get the current organization from thread-local storage."""
    return getattr(_thread_locals, "organization", None)


def set_current_organization(organization: Optional[Organization]) -> None:
    """Set the current organization in thread-local storage."""
    _thread_locals.organization = organization


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware that sets the current organization based on the logged-in user.
    """

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        # Reset organization at start of request
        set_current_organization(None)

        # Skip for unauthenticated users
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        # Get organization from user
        user = request.user
        if hasattr(user, "organization") and user.organization:
            organization = user.organization

            # Check if organization is active
            if not organization.is_active:
                from django.contrib.auth import logout
                logout(request)
                return None

            # Set organization in thread-local and request
            set_current_organization(organization)
            request.organization = organization
        else:
            request.organization = None

        return None

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        # Clear organization at end of request
        set_current_organization(None)
        return response


class OrganizationRequiredMiddleware(MiddlewareMixin):
    """
    Middleware that ensures user has an organization for protected views.
    """

    EXEMPT_URLS = [
        "/admin/",
        "/accounts/",
        "/auth/",
        "/__debug__/",
        "/health/",
        "/static/",
        "/media/",
    ]

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        # Check if URL is exempt
        path = request.path
        for exempt_url in self.EXEMPT_URLS:
            if path.startswith(exempt_url):
                return None

        # Check if user is authenticated and has organization
        if request.user.is_authenticated:
            if not hasattr(request, "organization") or not request.organization:
                # Redirect to organization setup or error page
                from django.shortcuts import redirect
                return redirect("core:no_organization")

        return None
