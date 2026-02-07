"""
Services pour le calcul des KPIs de vente.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from apps.invoicing.models import Invoice, Quote
from apps.crm.models import Company, Opportunity


class SalesAnalyticsService:
    """Service d'analyse des ventes."""

    @staticmethod
    def get_revenue_stats(organization, start_date=None, end_date=None):
        """
        Calcule les statistiques de chiffre d'affaires.

        Returns dict with:
        - total_revenue: CA total TTC
        - total_ht: CA total HT
        - total_vat: TVA totale
        - invoice_count: Nombre de factures
        - average_invoice: Montant moyen par facture
        - paid_amount: Montant encaissé
        - unpaid_amount: Montant restant à encaisser
        """
        if end_date is None:
            end_date = timezone.now().date()
        if start_date is None:
            start_date = date(end_date.year, 1, 1)

        invoices = Invoice.objects.filter(
            organization=organization,
            issue_date__gte=start_date,
            issue_date__lte=end_date,
            status__in=['sent', 'paid', 'partial', 'overdue']
        )

        total_ht = invoices.aggregate(total=Sum('total_ht'))['total'] or Decimal('0')
        total_vat = invoices.aggregate(total=Sum('total_vat'))['total'] or Decimal('0')
        total_ttc = invoices.aggregate(total=Sum('total_ttc'))['total'] or Decimal('0')
        paid_amount = invoices.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        invoice_count = invoices.count()

        return {
            'total_revenue': total_ttc,
            'total_ht': total_ht,
            'total_vat': total_vat,
            'invoice_count': invoice_count,
            'average_invoice': total_ttc / invoice_count if invoice_count > 0 else Decimal('0'),
            'paid_amount': paid_amount,
            'unpaid_amount': total_ttc - paid_amount,
            'payment_rate': (paid_amount / total_ttc * 100) if total_ttc > 0 else Decimal('0'),
        }

    @staticmethod
    def get_quotes_stats(organization, start_date=None, end_date=None):
        """
        Calcule les statistiques des devis.

        Returns dict with:
        - total_sent: Nombre de devis envoyés
        - total_accepted: Nombre de devis acceptés
        - total_rejected: Nombre de devis refusés
        - total_pending: Nombre de devis en attente
        - conversion_rate: Taux de conversion
        - total_value: Valeur totale des devis
        - average_value: Valeur moyenne des devis
        """
        if end_date is None:
            end_date = timezone.now().date()
        if start_date is None:
            start_date = date(end_date.year, 1, 1)

        quotes = Quote.objects.filter(
            organization=organization,
            issue_date__gte=start_date,
            issue_date__lte=end_date
        )

        total_count = quotes.count()
        sent = quotes.filter(status__in=['sent', 'accepted', 'rejected', 'invoiced']).count()
        accepted = quotes.filter(status__in=['accepted', 'invoiced']).count()
        rejected = quotes.filter(status='rejected').count()
        pending = quotes.filter(status__in=['draft', 'sent']).count()

        total_value = quotes.aggregate(total=Sum('total_ttc'))['total'] or Decimal('0')
        accepted_value = quotes.filter(
            status__in=['accepted', 'invoiced']
        ).aggregate(total=Sum('total_ttc'))['total'] or Decimal('0')

        return {
            'total_count': total_count,
            'total_sent': sent,
            'total_accepted': accepted,
            'total_rejected': rejected,
            'total_pending': pending,
            'conversion_rate': (accepted / sent * 100) if sent > 0 else Decimal('0'),
            'total_value': total_value,
            'accepted_value': accepted_value,
            'average_value': total_value / total_count if total_count > 0 else Decimal('0'),
        }

    @staticmethod
    def get_monthly_revenue(organization, year=None, months=12):
        """
        Récupère le CA mensuel.

        Returns list of dicts with:
        - month: Mois (datetime)
        - revenue: CA du mois
        - invoice_count: Nombre de factures
        """
        if year is None:
            year = timezone.now().year

        end_date = date(year, 12, 31)
        start_date = end_date - timedelta(days=months * 31)

        invoices = Invoice.objects.filter(
            organization=organization,
            issue_date__gte=start_date,
            issue_date__lte=end_date,
            status__in=['sent', 'paid', 'partial', 'overdue']
        ).annotate(
            month=TruncMonth('issue_date')
        ).values('month').annotate(
            revenue=Sum('total_ttc'),
            invoice_count=Count('id')
        ).order_by('month')

        return list(invoices)

    @staticmethod
    def get_top_clients(organization, start_date=None, end_date=None, limit=10):
        """
        Récupère les meilleurs clients par CA.

        Returns list of dicts with:
        - company: Entreprise
        - revenue: CA total
        - invoice_count: Nombre de factures
        """
        if end_date is None:
            end_date = timezone.now().date()
        if start_date is None:
            start_date = date(end_date.year, 1, 1)

        clients = Invoice.objects.filter(
            organization=organization,
            issue_date__gte=start_date,
            issue_date__lte=end_date,
            status__in=['sent', 'paid', 'partial', 'overdue']
        ).values(
            'company__id', 'company__name'
        ).annotate(
            revenue=Sum('total_ttc'),
            invoice_count=Count('id')
        ).order_by('-revenue')[:limit]

        return list(clients)

    @staticmethod
    def get_payment_delays(organization, start_date=None, end_date=None):
        """
        Calcule les délais de paiement moyens.

        Returns dict with:
        - average_delay: Délai moyen en jours
        - on_time_count: Factures payées à temps
        - late_count: Factures payées en retard
        - on_time_rate: Taux de paiement à temps
        """
        if end_date is None:
            end_date = timezone.now().date()
        if start_date is None:
            start_date = date(end_date.year, 1, 1)

        paid_invoices = Invoice.objects.filter(
            organization=organization,
            issue_date__gte=start_date,
            issue_date__lte=end_date,
            status='paid'
        )

        total_paid = paid_invoices.count()
        on_time = 0
        late = 0
        total_delay_days = 0

        for invoice in paid_invoices:
            # Get last payment date
            last_payment = invoice.payments.order_by('-payment_date').first()
            if last_payment:
                delay = (last_payment.payment_date - invoice.due_date).days
                total_delay_days += max(0, delay)
                if delay <= 0:
                    on_time += 1
                else:
                    late += 1

        return {
            'average_delay': total_delay_days / total_paid if total_paid > 0 else 0,
            'on_time_count': on_time,
            'late_count': late,
            'on_time_rate': (on_time / total_paid * 100) if total_paid > 0 else 0,
        }

    @staticmethod
    def get_overdue_summary(organization):
        """
        Résumé des impayés.

        Returns dict with:
        - total_overdue: Montant total en retard
        - overdue_count: Nombre de factures en retard
        - by_age: Répartition par ancienneté
        """
        today = timezone.now().date()

        overdue = Invoice.objects.filter(
            organization=organization,
            status__in=['sent', 'partial', 'overdue'],
            due_date__lt=today
        )

        total_overdue = sum(inv.balance_due for inv in overdue)
        overdue_count = overdue.count()

        # Group by age
        age_0_30 = sum(
            inv.balance_due for inv in overdue
            if (today - inv.due_date).days <= 30
        )
        age_31_60 = sum(
            inv.balance_due for inv in overdue
            if 30 < (today - inv.due_date).days <= 60
        )
        age_61_90 = sum(
            inv.balance_due for inv in overdue
            if 60 < (today - inv.due_date).days <= 90
        )
        age_90_plus = sum(
            inv.balance_due for inv in overdue
            if (today - inv.due_date).days > 90
        )

        return {
            'total_overdue': total_overdue,
            'overdue_count': overdue_count,
            'by_age': {
                '0_30': age_0_30,
                '31_60': age_31_60,
                '61_90': age_61_90,
                '90_plus': age_90_plus,
            }
        }

    @staticmethod
    def get_opportunities_pipeline(organization):
        """
        Résumé du pipeline d'opportunités.

        Returns dict with:
        - total_value: Valeur totale du pipeline
        - by_stage: Répartition par étape
        - weighted_value: Valeur pondérée (avec probabilités)
        """
        # Filter open opportunities (not won and not lost)
        opportunities = Opportunity.objects.filter(
            organization=organization,
            stage__is_won=False,
            stage__is_lost=False
        ).select_related('stage')

        total_value = sum(opp.amount or 0 for opp in opportunities)

        by_stage = {}
        for opp in opportunities:
            stage_name = opp.stage.name if opp.stage else 'Sans étape'
            probability = opp.stage.probability if opp.stage else 0

            if stage_name not in by_stage:
                by_stage[stage_name] = {
                    'count': 0,
                    'value': Decimal('0'),
                    'weighted_value': Decimal('0'),
                    'probability': probability,
                }

            by_stage[stage_name]['count'] += 1
            by_stage[stage_name]['value'] += opp.amount or 0
            by_stage[stage_name]['weighted_value'] += (opp.amount or 0) * Decimal(str(probability / 100))

        weighted_value = sum(stage['weighted_value'] for stage in by_stage.values())

        return {
            'total_value': total_value,
            'weighted_value': weighted_value,
            'opportunity_count': opportunities.count(),
            'by_stage': by_stage,
        }

    @staticmethod
    def get_comparison_period(organization, current_start, current_end):
        """
        Compare avec la période précédente.

        Returns dict with growth rates.
        """
        # Calculate previous period
        period_days = (current_end - current_start).days
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=period_days)

        current_stats = SalesAnalyticsService.get_revenue_stats(
            organization, current_start, current_end
        )
        previous_stats = SalesAnalyticsService.get_revenue_stats(
            organization, previous_start, previous_end
        )

        def calc_growth(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return ((current - previous) / previous * 100)

        return {
            'current': current_stats,
            'previous': previous_stats,
            'revenue_growth': calc_growth(
                current_stats['total_revenue'],
                previous_stats['total_revenue']
            ),
            'invoice_count_growth': calc_growth(
                current_stats['invoice_count'],
                previous_stats['invoice_count']
            ),
            'average_invoice_growth': calc_growth(
                current_stats['average_invoice'],
                previous_stats['average_invoice']
            ),
        }
