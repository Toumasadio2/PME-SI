"""
Account views.
"""
import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetConfirmView,
)
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    ProfileForm,
    TwoFactorSetupForm,
    TwoFactorVerifyForm,
)

User = get_user_model()


class CustomLoginView(LoginView):
    """Custom login view."""

    form_class = CustomAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()

        # Check if 2FA is enabled
        if user.is_2fa_enabled:
            # Store user ID in session for 2FA verification
            self.request.session["2fa_user_id"] = str(user.id)
            return redirect("accounts:2fa_verify")

        response = super().form_valid(form)

        # Check for pending invitation
        pending_token = self.request.session.pop("pending_invitation", None)
        if pending_token:
            return redirect("accounts:accept_invitation", token=pending_token)

        return response


class CustomLogoutView(LogoutView):
    """Custom logout view."""

    next_page = reverse_lazy("core:home")


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view."""

    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/emails/password_reset_email.html"
    success_url = reverse_lazy("accounts:password_reset_done")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view."""

    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


@require_http_methods(["GET", "POST"])
def register(request: HttpRequest) -> HttpResponse:
    """User registration view."""
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Bienvenue ! Votre compte a été créé avec succès.")
            return redirect("dashboard:index")
    else:
        form = CustomUserCreationForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def profile(request: HttpRequest) -> HttpResponse:
    """User profile view."""
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def setup_2fa(request: HttpRequest) -> HttpResponse:
    """Setup two-factor authentication."""
    user = request.user

    # Generate new secret if not exists
    if not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        user.save(update_fields=["totp_secret"])

    totp = pyotp.TOTP(user.totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name="PME-SI"
    )

    # Generate QR code as SVG
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    buffer = BytesIO()
    img.save(buffer)
    qr_code_svg = buffer.getvalue().decode()

    if request.method == "POST":
        form = TwoFactorSetupForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            if totp.verify(code):
                user.is_2fa_enabled = True
                user.save(update_fields=["is_2fa_enabled"])
                messages.success(request, "L'authentification à deux facteurs a été activée.")
                return redirect("accounts:profile")
            else:
                form.add_error("code", "Code invalide. Veuillez réessayer.")
    else:
        form = TwoFactorSetupForm()

    return render(request, "accounts/setup_2fa.html", {
        "form": form,
        "qr_code_svg": qr_code_svg,
        "secret": user.totp_secret,
    })


@login_required
@require_http_methods(["POST"])
def disable_2fa(request: HttpRequest) -> HttpResponse:
    """Disable two-factor authentication."""
    user = request.user
    user.is_2fa_enabled = False
    user.totp_secret = ""
    user.save(update_fields=["is_2fa_enabled", "totp_secret"])
    messages.success(request, "L'authentification à deux facteurs a été désactivée.")
    return redirect("accounts:profile")


@require_http_methods(["GET", "POST"])
def verify_2fa(request: HttpRequest) -> HttpResponse:
    """Verify 2FA code during login."""
    user_id = request.session.get("2fa_user_id")
    if not user_id:
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        del request.session["2fa_user_id"]
        return redirect("accounts:login")

    if request.method == "POST":
        form = TwoFactorVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            totp = pyotp.TOTP(user.totp_secret)
            if totp.verify(code):
                del request.session["2fa_user_id"]
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                messages.success(request, f"Bienvenue, {user.get_short_name()} !")
                return redirect("dashboard:index")
            else:
                form.add_error("code", "Code invalide. Veuillez réessayer.")
    else:
        form = TwoFactorVerifyForm()

    return render(request, "accounts/verify_2fa.html", {"form": form})
