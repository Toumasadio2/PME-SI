"""
Notification views.
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST, require_GET

from .models import Notification
from .services import NotificationService


@login_required
@require_GET
def notification_list(request: HttpRequest) -> HttpResponse:
    """List all notifications for the current user."""
    notifications = Notification.objects.filter(user=request.user)

    # Filter by read status
    status = request.GET.get("status")
    if status == "unread":
        notifications = notifications.filter(is_read=False)
    elif status == "read":
        notifications = notifications.filter(is_read=True)

    # Filter by category
    category = request.GET.get("category")
    if category:
        notifications = notifications.filter(category=category)

    notifications = notifications[:50]

    if request.headers.get("HX-Request"):
        return render(request, "notifications/partials/list.html", {
            "notifications": notifications,
        })

    return render(request, "notifications/list.html", {
        "notifications": notifications,
    })


@login_required
@require_GET
def notification_dropdown(request: HttpRequest) -> HttpResponse:
    """Get notifications for the dropdown menu (HTMX)."""
    notifications = Notification.objects.filter(
        user=request.user
    )[:10]

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return render(request, "notifications/partials/dropdown.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })


@login_required
@require_POST
def mark_as_read(request: HttpRequest, notification_id: str) -> HttpResponse:
    """Mark a single notification as read."""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.mark_as_read()

    if request.headers.get("HX-Request"):
        return HttpResponse(status=204)

    return JsonResponse({"status": "ok"})


@login_required
@require_POST
def mark_all_as_read(request: HttpRequest) -> HttpResponse:
    """Mark all notifications as read."""
    count = NotificationService.mark_all_as_read(request.user)

    if request.headers.get("HX-Request"):
        return render(request, "notifications/partials/dropdown.html", {
            "notifications": [],
            "unread_count": 0,
        })

    return JsonResponse({"status": "ok", "marked": count})


@login_required
@require_GET
def unread_count(request: HttpRequest) -> JsonResponse:
    """Get unread notification count (for polling)."""
    count = NotificationService.get_unread_count(request.user)
    return JsonResponse({"count": count})
