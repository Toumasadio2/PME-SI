"""
Service d'envoi d'emails pour les comptes utilisateurs.
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse


class InvitationEmailService:
    """Service d'envoi d'emails d'invitation."""

    @classmethod
    def send_invitation(cls, invitation, request=None):
        """
        Envoie un email d'invitation à rejoindre une organisation.

        Args:
            invitation: Instance de UserInvitation
            request: HttpRequest pour construire l'URL absolue

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        # Build invitation URL
        if request:
            base_url = request.build_absolute_uri('/')[:-1]
        else:
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

        invitation_url = f"{base_url}/auth/invitation/{invitation.token}/"

        # Prepare email content
        context = {
            'invitation': invitation,
            'organization': invitation.organization,
            'invited_by': invitation.invited_by,
            'invitation_url': invitation_url,
            'expires_at': invitation.expires_at,
        }

        subject = f"Invitation à rejoindre {invitation.organization.name}"
        text_content = render_to_string('accounts/emails/invitation.txt', context)
        html_content = render_to_string('accounts/emails/invitation.html', context)

        # Create and send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invitation.email],
        )
        email.attach_alternative(html_content, "text/html")

        sent = email.send(fail_silently=False)
        return bool(sent)
