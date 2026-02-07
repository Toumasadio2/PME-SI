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
from django.db.models import Q

from apps.permissions.models import Role

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


class InviteMemberForm(forms.Form):
    """Form for inviting a new team member."""

    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            "placeholder": "nouveau.membre@example.com",
        }),
    )
    role = forms.ModelChoiceField(
        label="Rôle",
        queryset=Role.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
        }),
    )
    is_organization_admin = forms.BooleanField(
        label="Administrateur de l'entreprise",
        required=False,
        help_text="Peut gérer les membres et les paramètres de l'entreprise.",
        widget=forms.CheckboxInput(attrs={
            "class": "h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500",
        }),
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields["role"].queryset = Role.objects.filter(
                Q(organization=organization) | Q(organization__isnull=True, is_system=True)
            )


class UserRoleForm(forms.Form):
    """Form for updating a user's roles."""

    roles = forms.ModelMultipleChoiceField(
        label="Rôles",
        queryset=Role.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            "class": "h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500",
        }),
    )
    is_organization_admin = forms.BooleanField(
        label="Administrateur de l'entreprise",
        required=False,
        help_text="Peut gérer les membres et les paramètres de l'entreprise.",
        widget=forms.CheckboxInput(attrs={
            "class": "h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500",
        }),
    )

    def __init__(self, *args, organization=None, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields["roles"].queryset = Role.objects.filter(
                Q(organization=organization) | Q(organization__isnull=True, is_system=True)
            )
        if instance:
            from apps.permissions.models import UserRole
            self.fields["is_organization_admin"].initial = instance.is_organization_admin
            current_roles = UserRole.objects.filter(
                user=instance, organization=organization
            ).values_list("role_id", flat=True)
            self.fields["roles"].initial = list(current_roles)
