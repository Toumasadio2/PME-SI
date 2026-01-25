"""
Template tags for permission checking.
"""
from django import template

from apps.permissions.services import PermissionService

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perm(context, codename: str) -> bool:
    """
    Check if current user has a permission.

    Usage:
        {% has_perm "crm_view" as can_view_crm %}
        {% if can_view_crm %}...{% endif %}
    """
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False
    return PermissionService.has_permission(request.user, codename)


@register.simple_tag(takes_context=True)
def has_module_perm(context, module: str) -> bool:
    """
    Check if current user has access to a module.

    Usage:
        {% has_module_perm "crm" as can_access_crm %}
    """
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False
    return PermissionService.has_module_permission(request.user, module)


@register.inclusion_tag("permissions/partials/if_perm.html", takes_context=True)
def if_perm(context, codename: str):
    """
    Render content only if user has permission.

    Usage:
        {% if_perm "crm_create" %}
            <button>Créer</button>
        {% endif_perm %}
    """
    request = context.get("request")
    has_permission = False
    if request and request.user.is_authenticated:
        has_permission = PermissionService.has_permission(request.user, codename)
    return {"has_permission": has_permission}
