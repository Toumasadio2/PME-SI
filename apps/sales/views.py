"""Views du module Ventes."""
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone

from .models import SalesTarget
from .forms import SalesTargetForm
from .services import SalesAnalyticsService


class SalesBaseMixin(LoginRequiredMixin):
    """Base mixin for Sales views with tenant filtering."""

    def get_organization(self):
        """Get current organization from request."""
        return getattr(self.request, 'organization', None)

    def get_queryset(self):
        """Filter by current organization."""
        qs = super().get_queryset()
        org = self.get_organization()
        if org:
            return qs.filter(organization=org)
        return qs.none()


class SalesDashboardView(SalesBaseMixin, TemplateView):
    """Dashboard principal des ventes avec KPIs."""
    template_name = 'sales/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()

        if not org:
            context['no_organization'] = True
            return context

        # Date range
        today = timezone.now().date()
        year_start = date(today.year, 1, 1)
        month_start = date(today.year, today.month, 1)

        # Get stats
        context['revenue_ytd'] = SalesAnalyticsService.get_revenue_stats(
            org, year_start, today
        )
        context['revenue_mtd'] = SalesAnalyticsService.get_revenue_stats(
            org, month_start, today
        )
        context['quotes_ytd'] = SalesAnalyticsService.get_quotes_stats(
            org, year_start, today
        )
        context['overdue'] = SalesAnalyticsService.get_overdue_summary(org)
        context['top_clients'] = SalesAnalyticsService.get_top_clients(
            org, year_start, today, limit=5
        )
        context['pipeline'] = SalesAnalyticsService.get_opportunities_pipeline(org)

        # Comparison with previous period (month)
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = date(prev_month_end.year, prev_month_end.month, 1)
        context['comparison'] = SalesAnalyticsService.get_comparison_period(
            org, month_start, today
        )

        # Active targets
        context['targets'] = SalesTarget.objects.filter(
            organization=org,
            is_active=True,
            year=today.year
        ).order_by('-period', 'target_type')[:5]

        context['current_year'] = today.year
        context['current_month'] = today.month

        return context


class RevenueChartAPIView(SalesBaseMixin, TemplateView):
    """API endpoint for revenue chart data."""
    template_name = 'sales/dashboard.html'  # Not used but required

    def get(self, request, *args, **kwargs):
        org = self.get_organization()
        if not org:
            return JsonResponse({'error': 'No organization'}, status=400)

        year = request.GET.get('year', timezone.now().year)
        try:
            year = int(year)
        except ValueError:
            year = timezone.now().year

        monthly_data = SalesAnalyticsService.get_monthly_revenue(org, year)

        # Format for Chart.js
        labels = []
        revenue_data = []
        invoice_count_data = []

        months_fr = [
            'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
            'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'
        ]

        for item in monthly_data:
            month_num = item['month'].month
            labels.append(months_fr[month_num - 1])
            revenue_data.append(float(item['revenue'] or 0))
            invoice_count_data.append(item['invoice_count'])

        return JsonResponse({
            'labels': labels,
            'datasets': [
                {
                    'label': 'Chiffre d\'affaires (€)',
                    'data': revenue_data,
                    'backgroundColor': 'rgba(37, 99, 235, 0.5)',
                    'borderColor': 'rgb(37, 99, 235)',
                    'borderWidth': 2,
                    'yAxisID': 'y',
                },
                {
                    'label': 'Nombre de factures',
                    'data': invoice_count_data,
                    'backgroundColor': 'rgba(16, 185, 129, 0.5)',
                    'borderColor': 'rgb(16, 185, 129)',
                    'borderWidth': 2,
                    'type': 'line',
                    'yAxisID': 'y1',
                }
            ]
        })


class QuotesChartAPIView(SalesBaseMixin, TemplateView):
    """API endpoint for quotes funnel chart data."""
    template_name = 'sales/dashboard.html'  # Not used but required

    def get(self, request, *args, **kwargs):
        org = self.get_organization()
        if not org:
            return JsonResponse({'error': 'No organization'}, status=400)

        today = timezone.now().date()
        year_start = date(today.year, 1, 1)

        stats = SalesAnalyticsService.get_quotes_stats(org, year_start, today)

        return JsonResponse({
            'labels': ['Envoyés', 'Acceptés', 'Refusés', 'En attente'],
            'datasets': [{
                'data': [
                    stats['total_sent'],
                    stats['total_accepted'],
                    stats['total_rejected'],
                    stats['total_pending']
                ],
                'backgroundColor': [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(251, 191, 36, 0.8)'
                ]
            }],
            'conversion_rate': float(stats['conversion_rate'])
        })


class SalesTargetListView(SalesBaseMixin, ListView):
    """Liste des objectifs de vente."""
    model = SalesTarget
    template_name = 'sales/target_list.html'
    context_object_name = 'targets'

    def get_queryset(self):
        qs = super().get_queryset()
        year = self.request.GET.get('year', timezone.now().year)
        return qs.filter(year=year).order_by('-period', 'target_type')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_year'] = int(
            self.request.GET.get('year', timezone.now().year)
        )
        context['years'] = range(
            timezone.now().year - 2,
            timezone.now().year + 2
        )
        return context


class SalesTargetDetailView(SalesBaseMixin, DetailView):
    """Détail d'un objectif de vente avec suivi de progression."""
    model = SalesTarget
    template_name = 'sales/target_detail.html'
    context_object_name = 'target'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        target = self.object

        # Calculate current progress
        if target.target_type == 'revenue':
            stats = SalesAnalyticsService.get_revenue_stats(
                org, target.start_date, target.end_date
            )
            context['current_value'] = stats.get('total_revenue', 0)
        elif target.target_type == 'invoices':
            stats = SalesAnalyticsService.get_revenue_stats(
                org, target.start_date, target.end_date
            )
            context['current_value'] = stats.get('invoice_count', 0)
        elif target.target_type == 'quotes':
            stats = SalesAnalyticsService.get_quotes_stats(
                org, target.start_date, target.end_date
            )
            context['current_value'] = stats.get('total_sent', 0)
        elif target.target_type == 'conversion':
            stats = SalesAnalyticsService.get_quotes_stats(
                org, target.start_date, target.end_date
            )
            context['current_value'] = stats.get('conversion_rate', 0)
        else:
            context['current_value'] = 0

        # Calculate progress percentage
        if target.target_value and target.target_value > 0:
            context['progress'] = min(
                100,
                round((float(context['current_value']) / float(target.target_value)) * 100, 1)
            )
        else:
            context['progress'] = 0

        return context


class SalesTargetCreateView(SalesBaseMixin, CreateView):
    """Création d'un objectif de vente."""
    model = SalesTarget
    form_class = SalesTargetForm
    template_name = 'sales/target_form.html'
    success_url = reverse_lazy('sales:target_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        messages.success(self.request, 'Objectif créé avec succès.')
        return super().form_valid(form)


class SalesTargetUpdateView(SalesBaseMixin, UpdateView):
    """Modification d'un objectif de vente."""
    model = SalesTarget
    form_class = SalesTargetForm
    template_name = 'sales/target_form.html'
    success_url = reverse_lazy('sales:target_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Objectif modifié avec succès.')
        return super().form_valid(form)


class SalesTargetDeleteView(SalesBaseMixin, DeleteView):
    """Suppression d'un objectif de vente."""
    model = SalesTarget
    template_name = 'sales/target_confirm_delete.html'
    success_url = reverse_lazy('sales:target_list')

    def form_valid(self, form):
        messages.success(self.request, 'Objectif supprimé.')
        return super().form_valid(form)
