"""
Modèles du module Ventes.
- Objectifs de vente
- KPIs
"""
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone

from apps.core.models import Organization
from apps.core.validators import validate_receipt_file


class SalesTarget(models.Model):
    """Objectif de vente."""

    PERIOD_CHOICES = [
        ('monthly', 'Mensuel'),
        ('quarterly', 'Trimestriel'),
        ('yearly', 'Annuel'),
    ]

    TARGET_TYPE_CHOICES = [
        ('revenue', 'Chiffre d\'affaires'),
        ('invoices', 'Nombre de factures'),
        ('quotes', 'Nombre de devis'),
        ('conversion', 'Taux de conversion'),
        ('new_clients', 'Nouveaux clients'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='sales_targets'
    )
    name = models.CharField('Nom', max_length=200)
    target_type = models.CharField(
        'Type d\'objectif',
        max_length=20,
        choices=TARGET_TYPE_CHOICES,
        default='revenue'
    )
    period = models.CharField(
        'Période',
        max_length=20,
        choices=PERIOD_CHOICES,
        default='monthly'
    )
    year = models.PositiveIntegerField('Année')
    month = models.PositiveIntegerField('Mois', null=True, blank=True)
    quarter = models.PositiveIntegerField('Trimestre', null=True, blank=True)

    target_value = models.DecimalField(
        'Valeur cible',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_targets',
        verbose_name='Assigné à'
    )

    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Objectif de vente'
        verbose_name_plural = 'Objectifs de vente'
        ordering = ['-year', '-month', '-quarter']

    def __str__(self):
        period_str = f"{self.year}"
        if self.period == 'monthly' and self.month:
            period_str = f"{self.month:02d}/{self.year}"
        elif self.period == 'quarterly' and self.quarter:
            period_str = f"T{self.quarter}/{self.year}"
        return f"{self.name} - {period_str}"

    @property
    def start_date(self):
        """Date de début de la période."""
        if self.period == 'yearly':
            return timezone.datetime(self.year, 1, 1).date()
        elif self.period == 'quarterly' and self.quarter:
            month = (self.quarter - 1) * 3 + 1
            return timezone.datetime(self.year, month, 1).date()
        elif self.period == 'monthly' and self.month:
            return timezone.datetime(self.year, self.month, 1).date()
        return timezone.datetime(self.year, 1, 1).date()

    @property
    def end_date(self):
        """Date de fin de la période."""
        from calendar import monthrange

        if self.period == 'yearly':
            return timezone.datetime(self.year, 12, 31).date()
        elif self.period == 'quarterly' and self.quarter:
            month = self.quarter * 3
            _, last_day = monthrange(self.year, month)
            return timezone.datetime(self.year, month, last_day).date()
        elif self.period == 'monthly' and self.month:
            _, last_day = monthrange(self.year, self.month)
            return timezone.datetime(self.year, self.month, last_day).date()
        return timezone.datetime(self.year, 12, 31).date()


class Expense(models.Model):
    """Dépense de l'entreprise."""

    CATEGORY_CHOICES = [
        ('salary', 'Salaires'),
        ('rent', 'Loyer'),
        ('utilities', 'Services (eau, électricité, internet)'),
        ('supplies', 'Fournitures'),
        ('transport', 'Transport'),
        ('marketing', 'Marketing'),
        ('equipment', 'Équipements'),
        ('maintenance', 'Maintenance'),
        ('taxes', 'Taxes et impôts'),
        ('insurance', 'Assurances'),
        ('other', 'Autres'),
    ]

    CURRENCY_CHOICES = [
        ('XOF', 'Franc CFA (XOF)'),
        ('EUR', 'Euro (€)'),
        ('USD', 'Dollar US ($)'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    description = models.CharField('Description', max_length=255)
    category = models.CharField(
        'Catégorie',
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    amount = models.DecimalField(
        'Montant',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        'Devise',
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='XOF'
    )
    date = models.DateField('Date')
    supplier = models.CharField('Fournisseur', max_length=200, blank=True)
    reference = models.CharField('Référence', max_length=100, blank=True)
    notes = models.TextField('Notes', blank=True)
    receipt = models.FileField(
        'Justificatif',
        upload_to='expenses/receipts/',
        null=True,
        blank=True,
        validators=[validate_receipt_file]
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_expenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dépense'
        verbose_name_plural = 'Dépenses'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} - {self.amount} {self.currency}"

    def get_currency_symbol(self):
        symbols = {'XOF': 'FCFA', 'EUR': '€', 'USD': '$'}
        return symbols.get(self.currency, self.currency)


class SalesKPI(models.Model):
    """KPI de vente calculé et stocké pour historique."""

    KPI_TYPE_CHOICES = [
        ('revenue_total', 'CA Total'),
        ('revenue_average', 'CA Moyen par facture'),
        ('quotes_sent', 'Devis envoyés'),
        ('quotes_accepted', 'Devis acceptés'),
        ('conversion_rate', 'Taux de conversion'),
        ('invoices_sent', 'Factures émises'),
        ('invoices_paid', 'Factures payées'),
        ('payment_rate', 'Taux de paiement'),
        ('average_payment_delay', 'Délai moyen de paiement'),
        ('overdue_amount', 'Montant en retard'),
        ('new_clients', 'Nouveaux clients'),
        ('active_opportunities', 'Opportunités actives'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='sales_kpis'
    )
    kpi_type = models.CharField(
        'Type de KPI',
        max_length=30,
        choices=KPI_TYPE_CHOICES
    )
    date = models.DateField('Date')
    value = models.DecimalField(
        'Valeur',
        max_digits=14,
        decimal_places=2
    )
    metadata = models.JSONField('Métadonnées', default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'KPI Ventes'
        verbose_name_plural = 'KPIs Ventes'
        ordering = ['-date', 'kpi_type']
        unique_together = ['organization', 'kpi_type', 'date']

    def __str__(self):
        return f"{self.get_kpi_type_display()} - {self.date}: {self.value}"
