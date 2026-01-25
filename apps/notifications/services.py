"""
Notification services.
"""
from typing import Optional, List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.core.models import Organization
from .models import Notification, NotificationPreference

User = get_user_model()


class NotificationService:
    """Service for creating and managing notifications."""

    @classmethod
    def create(
        cls,
        user: User,
        title: str,
        message: str,
        notification_type: str = Notification.Type.INFO,
        category: str = Notification.Category.SYSTEM,
        organization: Optional[Organization] = None,
        link: str = "",
        related_object_type: str = "",
        related_object_id: str = "",
        send_email: bool = True,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification.objects.create(
            user=user,
            organization=organization or user.organization,
            title=title,
            message=message,
            notification_type=notification_type,
            category=category,
            link=link,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
        )

        # Send email if enabled
        if send_email:
            cls._send_email_notification(notification)

        return notification

    @classmethod
    def create_for_users(
        cls,
        users: List[User],
        title: str,
        message: str,
        **kwargs
    ) -> List[Notification]:
        """Create notifications for multiple users."""
        notifications = []
        for user in users:
            notification = cls.create(user=user, title=title, message=message, **kwargs)
            notifications.append(notification)
        return notifications

    @classmethod
    def get_unread_count(cls, user: User) -> int:
        """Get count of unread notifications for a user."""
        return Notification.objects.filter(user=user, is_read=False).count()

    @classmethod
    def mark_all_as_read(cls, user: User) -> int:
        """Mark all notifications as read for a user."""
        from django.utils import timezone
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

    @classmethod
    def _send_email_notification(cls, notification: Notification) -> None:
        """Send email notification if user preferences allow."""
        try:
            prefs = notification.user.notification_preferences
            if not prefs.should_send_email(notification.category):
                return
        except NotificationPreference.DoesNotExist:
            pass  # Default to sending email

        # Render email template
        context = {
            "notification": notification,
            "user": notification.user,
        }
        html_content = render_to_string(
            "notifications/emails/notification.html",
            context
        )
        text_content = render_to_string(
            "notifications/emails/notification.txt",
            context
        )

        try:
            send_mail(
                subject=notification.title,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                html_message=html_content,
                fail_silently=True,
            )
            notification.email_sent = True
            from django.utils import timezone
            notification.email_sent_at = timezone.now()
            notification.save(update_fields=["email_sent", "email_sent_at"])
        except Exception:
            pass  # Log error in production
