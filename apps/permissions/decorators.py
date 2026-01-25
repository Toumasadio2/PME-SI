"""
Permission decorators for views.
"""
from functools import wraps
from typing import List, Optional, Union

from django.http import HttpRequest, HttpResponseForbidden
from django.shortcuts import redirect

from .services import PermissionService


def permission_required(
    codename: Union[str, List[str]],
    redirect_url: Optional[str] = None,
    raise_exception: bool = False
):
    """
    Decorator to check if user has required permission(s).

    Usage:
        @permission_required("crm_view")
        def my_view(request):
            ...

        @permission_required(["crm_view", "crm_edit"])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not request.user.is_authenticated:
                if redirect_url:
                    return redirect(redirect_url)
                return HttpResponseForbidden("Non authentifié")

            codenames = [codename] if isinstance(codename, str) else codename

            has_perm = all(
                PermissionService.has_permission(request.user, c)
                for c in codenames
            )

            if not has_perm:
                if raise_exception:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied("Permission refusée")
                if redirect_url:
                    return redirect(redirect_url)
                return HttpResponseForbidden("Permission refusée")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def module_permission_required(module: str, redirect_url: Optional[str] = None):
    """
    Decorator to check if user has any permission in a module.

    Usage:
        @module_permission_required("crm")
        def crm_dashboard(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not request.user.is_authenticated:
                if redirect_url:
                    return redirect(redirect_url)
                return HttpResponseForbidden("Non authentifié")

            if not PermissionService.has_module_permission(request.user, module):
                if redirect_url:
                    return redirect(redirect_url)
                return HttpResponseForbidden("Permission refusée")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
