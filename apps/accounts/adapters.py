"""
Custom allauth adapters.
"""
from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpRequest


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
