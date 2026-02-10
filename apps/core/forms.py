"""
Core forms.
"""
from django import forms

from apps.accounts.models import User
from .models import Organization


class OrganizationSettingsForm(forms.ModelForm):
    """Form for organization settings."""

    class Meta:
        model = Organization
        fields = [
            "name",
            "siret",
            "address",
            "city",
            "postal_code",
            "country",
            "phone",
            "email",
            "website",
            "logo",
            "primary_color",
            "secondary_color",
            "document_template",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            }),
            "siret": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "12345678901234",
            }),
            "address": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "rows": 2,
            }),
            "city": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            }),
            "postal_code": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            }),
            "country": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            }),
            "phone": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "+33 1 23 45 67 89",
            }),
            "email": forms.EmailInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            }),
            "website": forms.URLInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "https://www.example.com",
            }),
            "logo": forms.FileInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "accept": "image/*",
            }),
            "primary_color": forms.TextInput(attrs={
                "type": "color",
                "class": "w-16 h-10 p-1 border border-gray-300 rounded-lg cursor-pointer",
            }),
            "secondary_color": forms.TextInput(attrs={
                "type": "color",
                "class": "w-16 h-10 p-1 border border-gray-300 rounded-lg cursor-pointer",
            }),
            "document_template": forms.RadioSelect(attrs={
                "class": "hidden",
            }),
        }
        labels = {
            "name": "Nom de l'entreprise",
            "siret": "SIRET",
            "address": "Adresse",
            "city": "Ville",
            "postal_code": "Code postal",
            "country": "Pays",
            "phone": "Téléphone",
            "email": "Email",
            "website": "Site web",
            "logo": "Logo",
            "primary_color": "Couleur principale",
            "secondary_color": "Couleur secondaire",
            "document_template": "Template des documents",
        }


class OrganizationCreateForm(forms.ModelForm):
    """Form for creating a new organization."""

    admin_email = forms.EmailField(
        label="Email de l'administrateur *",
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            "placeholder": "admin@entreprise.com",
        }),
        help_text="Un compte sera créé et l'utilisateur recevra ses identifiants."
    )

    admin_first_name = forms.CharField(
        label="Prénom de l'administrateur",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            "placeholder": "Jean",
        }),
    )

    admin_last_name = forms.CharField(
        label="Nom de l'administrateur",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            "placeholder": "Dupont",
        }),
    )

    class Meta:
        model = Organization
        fields = [
            "name",
            "siret",
            "email",
            "phone",
            "address",
            "city",
            "postal_code",
            "country",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Nom de l'entreprise",
            }),
            "siret": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "12345678901234",
            }),
            "email": forms.EmailInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "contact@entreprise.com",
            }),
            "phone": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "+33 1 23 45 67 89",
            }),
            "address": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "rows": 2,
            }),
            "city": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            }),
            "postal_code": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            }),
            "country": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "France",
            }),
        }
        labels = {
            "name": "Nom de l'entreprise *",
            "siret": "SIRET",
            "email": "Email de l'entreprise",
            "phone": "Téléphone",
            "address": "Adresse",
            "city": "Ville",
            "postal_code": "Code postal",
            "country": "Pays",
        }

    def clean_admin_email(self):
        email = self.cleaned_data.get('admin_email')
        if email:
            # Check if user already exists with super_admin status
            existing = User.objects.filter(email=email, is_super_admin=True).first()
            if existing:
                raise forms.ValidationError("Cet email appartient à un super administrateur.")
        return email


class AssignAdminForm(forms.Form):
    """Form for assigning an admin to an organization."""

    user = forms.ModelChoiceField(
        label="Utilisateur",
        queryset=User.objects.none(),
        widget=forms.Select(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
        }),
    )
    email = forms.EmailField(
        label="Ou créer un nouvel utilisateur (email)",
        required=False,
        widget=forms.EmailInput(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            "placeholder": "admin@exemple.com",
        }),
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization

        # All users can be selected (super admin perspective)
        self.fields['user'].queryset = User.objects.filter(
            is_active=True
        ).exclude(
            is_super_admin=True
        ).order_by('email')

        self.fields['user'].required = False

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        email = cleaned_data.get('email')

        if not user and not email:
            raise forms.ValidationError(
                "Veuillez sélectionner un utilisateur existant ou entrer un email pour en créer un nouveau."
            )

        if not user and email:
            # Check if user with this email exists
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                cleaned_data['user'] = existing_user
            else:
                # Create new user
                new_user = User.objects.create_user(
                    email=email,
                    password=User.objects.make_random_password(),
                )
                cleaned_data['user'] = new_user

        return cleaned_data
