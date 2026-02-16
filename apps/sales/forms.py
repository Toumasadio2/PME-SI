"""Formulaires du module Ventes."""
from django import forms
from django.utils import timezone

from .models import SalesTarget, Expense


class SalesTargetForm(forms.ModelForm):
    """Formulaire pour les objectifs de vente."""

    class Meta:
        model = SalesTarget
        fields = [
            'name', 'target_type', 'period', 'year', 'month', 'quarter',
            'target_value', 'assigned_to', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Objectif CA Q1 2025'
            }),
            'target_type': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.Select(attrs={
                'class': 'form-select',
                'x-model': 'period',
                '@change': 'updatePeriodFields()'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': timezone.now().year - 1,
                'max': timezone.now().year + 5
            }),
            'month': forms.Select(attrs={
                'class': 'form-select',
                'x-show': "period === 'monthly'"
            }, choices=[('', '---')] + [(i, f'{i:02d}') for i in range(1, 13)]),
            'quarter': forms.Select(attrs={
                'class': 'form-select',
                'x-show': "period === 'quarterly'"
            }, choices=[('', '---')] + [(i, f'T{i}') for i in range(1, 5)]),
            'target_value': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization

        # Set default year
        if not self.instance.pk:
            self.fields['year'].initial = timezone.now().year

        # Filter assigned_to by organization members if available
        if organization:
            from apps.accounts.models import OrganizationMembership
            member_ids = OrganizationMembership.objects.filter(
                organization=organization,
                is_active=True
            ).values_list('user_id', flat=True)
            self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.filter(
                id__in=member_ids
            )

    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        month = cleaned_data.get('month')
        quarter = cleaned_data.get('quarter')

        if period == 'monthly' and not month:
            self.add_error('month', 'Le mois est requis pour un objectif mensuel.')
        elif period == 'quarterly' and not quarter:
            self.add_error('quarter', 'Le trimestre est requis pour un objectif trimestriel.')

        # Clear unnecessary fields
        if period == 'yearly':
            cleaned_data['month'] = None
            cleaned_data['quarter'] = None
        elif period == 'monthly':
            cleaned_data['quarter'] = None
        elif period == 'quarterly':
            cleaned_data['month'] = None

        return cleaned_data


class ExpenseForm(forms.ModelForm):
    """Formulaire pour les dépenses."""

    class Meta:
        model = Expense
        fields = [
            'description', 'category', 'amount', 'currency', 'date',
            'supplier', 'reference', 'notes', 'receipt'
        ]
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Facture électricité janvier'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom du fournisseur'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Numéro de facture, référence...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Notes additionnelles...'
            }),
            'receipt': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*,.pdf'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()
