"""
Permission mixins for class-based views.
"""
from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseForbidden

from .services import PermissionService


class PermissionRequiredMixin(AccessMixin):
    """
    Mixin for views that require specific permission(s).

    Usage:
        class MyView(PermissionRequiredMixin, View):
            permission_required = "crm_view"
            # or
            permission_required = ["crm_view", "crm_edit"]
    """

    permission_required = None

    def has_permission(self) -> bool:
        if not self.request.user.is_authenticated:
            return False

        if self.permission_required is None:
            return True

        perms = self.permission_required
        if isinstance(perms, str):
            perms = [perms]

        return all(
            PermissionService.has_permission(self.request.user, p)
            for p in perms
        )

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ModulePermissionMixin(AccessMixin):
    """
    Mixin for views that require access to a module.

    Usage:
        class CRMDashboard(ModulePermissionMixin, View):
            module_required = "crm"
    """

    module_required = None

    def has_permission(self) -> bool:
        if not self.request.user.is_authenticated:
            return False

        if self.module_required is None:
            return True

        return PermissionService.has_module_permission(
            self.request.user,
            self.module_required
        )

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
