"""
Services pour le module de facturation.
- Génération de numéros séquentiels
- Conversion devis -> facture
- Génération PDF
"""
from datetime import date
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from .models import Quote, QuoteItem, Invoice, InvoiceItem


class NumberingService:
    """Service de numérotation automatique légale."""

    @staticmethod
    def generate_quote_number(organization):
        """
        Génère un numéro de devis unique.
        Format: DEV-YYYYMM-XXXX
        """
        today = timezone.now()
        prefix = f"DEV-{today.strftime('%Y%m')}-"

        # Get the last quote number for this month
        last_quote = Quote.objects.filter(
            organization=organization,
            number__startswith=prefix
        ).order_by('-number').first()

        if last_quote:
            try:
                last_num = int(last_quote.number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    @staticmethod
    def generate_invoice_number(organization):
        """
        Génère un numéro de facture unique et séquentiel.
        Format: FAC-YYYY-XXXXX (séquentiel annuel pour conformité légale)

        Important: La numérotation des factures doit être séquentielle
        et sans rupture conformément à la législation française.
        """
        year = timezone.now().year
        prefix = f"FAC-{year}-"

        # Get the last invoice number for this year
        last_invoice = Invoice.objects.filter(
            organization=organization,
            number__startswith=prefix
        ).order_by('-number').first()

        if last_invoice:
            try:
                last_num = int(last_invoice.number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:05d}"


class QuoteService:
    """Service pour les opérations sur les devis."""

    @staticmethod
    @transaction.atomic
    def create_quote(organization, company, subject, items_data, **kwargs):
        """Crée un devis avec ses lignes."""
        number = NumberingService.generate_quote_number(organization)

        quote = Quote.objects.create(
            organization=organization,
            number=number,
            company=company,
            subject=subject,
            **kwargs
        )

        for position, item_data in enumerate(items_data):
            QuoteItem.objects.create(
                quote=quote,
                position=position,
                **item_data
            )

        quote.calculate_totals()
        return quote

    @staticmethod
    @transaction.atomic
    def convert_to_invoice(quote, created_by=None):
        """
        Convertit un devis accepté en facture.
        Returns: Invoice object
        """
        if not quote.can_convert_to_invoice():
            raise ValueError("Ce devis ne peut pas être converti en facture.")

        number = NumberingService.generate_invoice_number(quote.organization)

        invoice = Invoice.objects.create(
            organization=quote.organization,
            number=number,
            # Client entreprise
            company=quote.company,
            contact=quote.contact,
            # Client particulier
            client_name=quote.client_name,
            client_email=quote.client_email,
            client_phone=quote.client_phone,
            client_address=quote.client_address,
            # Autres informations
            quote=quote,
            subject=quote.subject,
            introduction=quote.introduction,
            conditions=quote.conditions,
            issue_date=timezone.now().date(),
            created_by=created_by,
        )

        # Copy quote items to invoice items
        for quote_item in quote.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                product=quote_item.product,
                description=quote_item.description,
                quantity=quote_item.quantity,
                unit=quote_item.unit,
                unit_price=quote_item.unit_price,
                vat_rate=quote_item.vat_rate,
                discount_percent=quote_item.discount_percent,
                position=quote_item.position,
            )

        invoice.calculate_totals()

        # Update quote status
        quote.status = 'invoiced'
        quote.save(update_fields=['status'])

        return invoice


class InvoiceService:
    """Service pour les opérations sur les factures."""

    @staticmethod
    @transaction.atomic
    def create_invoice(organization, company, subject, items_data, **kwargs):
        """Crée une facture avec ses lignes."""
        number = NumberingService.generate_invoice_number(organization)

        invoice = Invoice.objects.create(
            organization=organization,
            number=number,
            company=company,
            subject=subject,
            **kwargs
        )

        for position, item_data in enumerate(items_data):
            InvoiceItem.objects.create(
                invoice=invoice,
                position=position,
                **item_data
            )

        invoice.calculate_totals()
        return invoice

    @staticmethod
    def get_overdue_invoices(organization, days_threshold=0):
        """Récupère les factures en retard."""
        threshold_date = timezone.now().date() - timezone.timedelta(days=days_threshold)
        return Invoice.objects.filter(
            organization=organization,
            status__in=['sent', 'partial', 'overdue'],
            due_date__lt=threshold_date
        ).order_by('due_date')

    @staticmethod
    def get_revenue_stats(organization, year=None):
        """Calcule les statistiques de chiffre d'affaires."""
        if year is None:
            year = timezone.now().year

        invoices = Invoice.objects.filter(
            organization=organization,
            issue_date__year=year,
            status__in=['sent', 'paid', 'partial']
        )

        total_ht = sum(inv.total_ht for inv in invoices)
        total_ttc = sum(inv.total_ttc for inv in invoices)
        total_paid = sum(inv.amount_paid for inv in invoices)
        total_unpaid = total_ttc - total_paid

        paid_invoices = invoices.filter(status='paid')
        unpaid_invoices = invoices.exclude(status='paid')

        return {
            'total_ht': total_ht,
            'total_ttc': total_ttc,
            'total_paid': total_paid,
            'total_unpaid': total_unpaid,
            'invoice_count': invoices.count(),
            'paid_count': paid_invoices.count(),
            'unpaid_count': unpaid_invoices.count(),
        }
