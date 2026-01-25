"""
Account URL configuration.
"""
from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),

    # Profile
    path("profile/", views.profile, name="profile"),

    # Two-factor authentication
    path("2fa/setup/", views.setup_2fa, name="setup_2fa"),
    path("2fa/disable/", views.disable_2fa, name="disable_2fa"),
    path("2fa/verify/", views.verify_2fa, name="2fa_verify"),

    # Password reset
    path(
        "password-reset/",
        views.CustomPasswordResetView.as_view(),
        name="password_reset"
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done"
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm"
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),
]
