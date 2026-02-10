"""
Custom allauth adapters.
"""
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import redirect


class NoSignupAccountAdapter(DefaultAccountAdapter):
    """Adapter that disables public signup."""

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        """
        Disable public signup. Users can only be invited.
        """
        # Check if this is an invitation-based signup
        if request.session.get("pending_invitation"):
            return True
        return False

    def respond_user_inactive(self, request, user):
        """Redirect inactive users to login."""
        messages.error(request, "Votre compte est inactif.")
        return redirect("accounts:login")

    def get_signup_redirect_url(self, request):
        """Redirect signup attempts to login."""
        messages.info(request, "L'inscription publique est désactivée. Contactez un administrateur pour obtenir une invitation.")
        return "accounts:login"
