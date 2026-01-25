"""
Core signals.
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import AuditLogEntry


def get_client_ip(request):
    """Get client IP from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login."""
    AuditLogEntry.objects.create(
        organization=getattr(user, "organization", None),
        user=user,
        action=AuditLogEntry.Action.LOGIN,
        model_name="User",
        object_id=str(user.pk),
        object_repr=str(user),
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout."""
    if user:
        AuditLogEntry.objects.create(
            organization=getattr(user, "organization", None),
            user=user,
            action=AuditLogEntry.Action.LOGOUT,
            model_name="User",
            object_id=str(user.pk),
            object_repr=str(user),
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
