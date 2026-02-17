"""CRM Forms."""
from django import forms
from django.utils import timezone

from .models import Activity, Company, Contact, Document, Opportunity, PipelineStage, Tag


class TagForm(forms.ModelForm):
    """Form for creating/editing tags."""

    class Meta:
        model = Tag
        fields = ["name", "color"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Nom du tag"
            }),
            "color": forms.TextInput(attrs={
                "type": "color",
                "class": "form-input h-10 w-20"
            }),
        }


class PipelineStageForm(forms.ModelForm):
    """Form for creating/editing pipeline stages."""

    class Meta:
        model = PipelineStage
        fields = ["name", "order", "probability", "color", "is_won", "is_lost"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Nom de l'étape"
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0
            }),
            "probability": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "max": 100
            }),
            "color": forms.TextInput(attrs={
                "type": "color",
                "class": "form-input h-10 w-20"
            }),
        }


class CompanyForm(forms.ModelForm):
    """Form for creating/editing companies."""

    class Meta:
        model = Company
        fields = [
            "name", "category", "siret", "vat_number",
            "address", "postal_code", "city", "country",
            "phone", "email", "website",
            "industry", "employees_count", "annual_revenue",
            "tags", "assigned_to", "notes"
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Raison sociale"
            }),
            "category": forms.Select(attrs={"class": "form-select"}),
            "siret": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "12345678901234"
            }),
            "vat_number": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "FR12345678901"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2,
                "placeholder": "Adresse complète"
            }),
            "postal_code": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "75001"
            }),
            "city": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Paris"
            }),
            "country": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "France"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "+33 1 23 45 67 89"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-input",
                "placeholder": "contact@entreprise.fr"
            }),
            "website": forms.URLInput(attrs={
                "class": "form-input",
                "placeholder": "https://www.entreprise.fr"
            }),
            "industry": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Secteur d'activité"
            }),
            "employees_count": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0
            }),
            "annual_revenue": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "step": "0.01"
            }),
            "tags": forms.SelectMultiple(attrs={
                "class": "form-multiselect"
            }),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Notes internes..."
            }),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        if organization:
            from apps.accounts.models import OrganizationMembership
            from django.contrib.auth import get_user_model
            User = get_user_model()
            member_ids = OrganizationMembership.objects.filter(
                organization=organization,
                is_active=True
            ).values_list('user_id', flat=True)
            self.fields["assigned_to"].queryset = User.objects.filter(id__in=member_ids)


class ContactForm(forms.ModelForm):
    """Form for creating/editing contacts."""

    class Meta:
        model = Contact
        fields = [
            "civility", "first_name", "last_name",
            "company", "job_title", "department",
            "email", "phone", "mobile",
            "address", "postal_code", "city", "country",
            "category", "tags", "assigned_to",
            "accepts_marketing", "preferred_contact_method",
            "notes"
        ]
        widgets = {
            "civility": forms.Select(attrs={"class": "form-select"}),
            "first_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Prénom"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Nom"
            }),
            "company": forms.Select(attrs={"class": "form-select"}),
            "job_title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Directeur Commercial"
            }),
            "department": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Commercial"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-input",
                "placeholder": "prenom.nom@entreprise.fr"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "+33 1 23 45 67 89"
            }),
            "mobile": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "+33 6 12 34 56 78"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2
            }),
            "postal_code": forms.TextInput(attrs={"class": "form-input"}),
            "city": forms.TextInput(attrs={"class": "form-input"}),
            "country": forms.TextInput(attrs={"class": "form-input"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-multiselect"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "preferred_contact_method": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3
            }),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        if organization:
            from apps.accounts.models import OrganizationMembership
            from django.contrib.auth import get_user_model
            User = get_user_model()
            member_ids = OrganizationMembership.objects.filter(
                organization=organization,
                is_active=True
            ).values_list('user_id', flat=True)
            self.fields["assigned_to"].queryset = User.objects.filter(id__in=member_ids)
            self.fields["company"].queryset = Company.objects.filter(organization=organization)
            self.fields["tags"].queryset = Tag.objects.filter(organization=organization)


class OpportunityForm(forms.ModelForm):
    """Form for creating/editing opportunities."""

    class Meta:
        model = Opportunity
        fields = [
            "name", "company", "contact", "stage",
            "amount", "probability", "expected_close_date",
            "priority", "source", "description", "next_step",
            "assigned_to"
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Nom de l'opportunité"
            }),
            "company": forms.Select(attrs={"class": "form-select"}),
            "contact": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "step": "0.01",
                "placeholder": "10000.00"
            }),
            "probability": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "max": 100,
                "placeholder": "50"
            }),
            "expected_close_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date"
            }),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "source": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Site web, Salon, Recommandation..."
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Description de l'opportunité..."
            }),
            "next_step": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Prochaine action à réaliser"
            }),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        if organization:
            from apps.accounts.models import OrganizationMembership
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Filter users by organization members
            member_ids = OrganizationMembership.objects.filter(
                organization=organization,
                is_active=True
            ).values_list('user_id', flat=True)
            self.fields["assigned_to"].queryset = User.objects.filter(id__in=member_ids)
            # Filter companies and contacts by organization
            self.fields["company"].queryset = Company.objects.filter(
                organization=organization
            )
            self.fields["contact"].queryset = Contact.objects.filter(
                organization=organization
            )
            self.fields["stage"].queryset = PipelineStage.objects.filter(
                organization=organization
            )


class OpportunityStageUpdateForm(forms.Form):
    """Form for updating opportunity stage (Kanban drag & drop)."""

    stage_id = forms.UUIDField()


class ActivityForm(forms.ModelForm):
    """Form for creating/editing activities."""

    class Meta:
        model = Activity
        fields = [
            "activity_type", "status", "subject", "description",
            "contact", "company", "opportunity",
            "scheduled_date", "duration_minutes", "reminder_date",
            "assigned_to"
        ]
        widgets = {
            "activity_type": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Sujet de l'activité"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Notes et détails..."
            }),
            "contact": forms.Select(attrs={"class": "form-select"}),
            "company": forms.Select(attrs={"class": "form-select"}),
            "opportunity": forms.Select(attrs={"class": "form-select"}),
            "scheduled_date": forms.DateTimeInput(attrs={
                "class": "form-input",
                "type": "datetime-local"
            }),
            "duration_minutes": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "placeholder": "30"
            }),
            "reminder_date": forms.DateTimeInput(attrs={
                "class": "form-input",
                "type": "datetime-local"
            }),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        if organization:
            from apps.accounts.models import OrganizationMembership
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Filter users by organization members
            member_ids = OrganizationMembership.objects.filter(
                organization=organization,
                is_active=True
            ).values_list('user_id', flat=True)
            self.fields["assigned_to"].queryset = User.objects.filter(id__in=member_ids)
            self.fields["contact"].queryset = Contact.objects.filter(
                organization=organization
            )
            self.fields["company"].queryset = Company.objects.filter(
                organization=organization
            )
            self.fields["opportunity"].queryset = Opportunity.objects.filter(
                organization=organization
            )

    def clean(self):
        cleaned_data = super().clean()
        contact = cleaned_data.get("contact")
        company = cleaned_data.get("company")
        opportunity = cleaned_data.get("opportunity")

        # At least one relation is required
        if not contact and not company and not opportunity:
            raise forms.ValidationError(
                "Vous devez associer l'activité à au moins un contact, "
                "une entreprise ou une opportunité."
            )

        return cleaned_data


class QuickActivityForm(forms.ModelForm):
    """Simplified form for quick activity logging."""

    class Meta:
        model = Activity
        fields = ["activity_type", "subject", "description"]
        widgets = {
            "activity_type": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Sujet"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2,
                "placeholder": "Notes..."
            }),
        }


class DocumentForm(forms.ModelForm):
    """Form for uploading documents."""

    class Meta:
        model = Document
        fields = ["name", "file", "description", "contact", "company", "opportunity"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Nom du document"
            }),
            "file": forms.FileInput(attrs={
                "class": "form-input"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2
            }),
            "contact": forms.Select(attrs={"class": "form-select"}),
            "company": forms.Select(attrs={"class": "form-select"}),
            "opportunity": forms.Select(attrs={"class": "form-select"}),
        }


class ContactSearchForm(forms.Form):
    """Form for searching contacts."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Rechercher un contact...",
            "hx-get": "",
            "hx-trigger": "keyup changed delay:300ms",
            "hx-target": "#contact-list",
        })
    )
    category = forms.ChoiceField(
        required=False,
        choices=[("", "Toutes catégories")] + list(Contact.Category.choices),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    company = forms.ModelChoiceField(
        required=False,
        queryset=Company.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        if organization:
            self.fields["company"].queryset = Company.objects.filter(
                organization=organization
            )


class CompanySearchForm(forms.Form):
    """Form for searching companies."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Rechercher une entreprise...",
            "hx-get": "",
            "hx-trigger": "keyup changed delay:300ms",
            "hx-target": "#company-list",
        })
    )
    category = forms.ChoiceField(
        required=False,
        choices=[("", "Toutes catégories")] + list(Company.Category.choices),
        widget=forms.Select(attrs={"class": "form-select"})
    )


class OpportunitySearchForm(forms.Form):
    """Form for searching opportunities."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Rechercher une opportunité..."
        })
    )
    stage = forms.ModelChoiceField(
        required=False,
        queryset=PipelineStage.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    assigned_to = forms.ChoiceField(
        required=False,
        choices=[("", "Tous les commerciaux")],
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        if organization:
            self.fields["stage"].queryset = PipelineStage.objects.filter(
                organization=organization
            )
            # Filter assigned_to by organization members
            from apps.accounts.models import OrganizationMembership
            from django.contrib.auth import get_user_model
            User = get_user_model()
            member_ids = OrganizationMembership.objects.filter(
                organization=organization,
                is_active=True
            ).values_list('user_id', flat=True)
            members = User.objects.filter(id__in=member_ids)
            self.fields["assigned_to"].choices = [("", "Tous les commerciaux")] + [
                (str(user.id), user.get_full_name() or user.email) for user in members
            ]
