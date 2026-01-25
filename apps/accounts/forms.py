"""
Account forms.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Registration form."""

    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "votre@email.com",
            "autocomplete": "email",
        }),
    )
    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "Prénom",
        }),
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "Nom",
        }),
    )
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "••••••••••",
            "autocomplete": "new-password",
        }),
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "••••••••••",
            "autocomplete": "new-password",
        }),
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password1", "password2"]


class CustomAuthenticationForm(AuthenticationForm):
    """Login form."""

    username = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "votre@email.com",
            "autocomplete": "email",
        }),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "••••••••••",
            "autocomplete": "current-password",
        }),
    )


class ProfileForm(forms.ModelForm):
    """User profile update form."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "avatar", "job_title"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "last_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "phone": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "job_title": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "avatar": forms.FileInput(attrs={"class": "file-input file-input-bordered w-full"}),
        }


class TwoFactorSetupForm(forms.Form):
    """Form for setting up 2FA."""

    code = forms.CharField(
        label="Code de vérification",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "class": "input input-bordered w-full text-center text-2xl tracking-widest",
            "placeholder": "000000",
            "autocomplete": "one-time-code",
            "inputmode": "numeric",
            "pattern": "[0-9]*",
        }),
    )


class TwoFactorVerifyForm(forms.Form):
    """Form for verifying 2FA code on login."""

    code = forms.CharField(
        label="Code d'authentification",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "class": "input input-bordered w-full text-center text-2xl tracking-widest",
            "placeholder": "000000",
            "autocomplete": "one-time-code",
            "inputmode": "numeric",
            "pattern": "[0-9]*",
            "autofocus": True,
        }),
    )
