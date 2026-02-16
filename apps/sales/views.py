"""Views du module Ventes."""
from datetime import date, timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum, Count

from apps.permissions.mixins import ModulePermissionMixin, PermissionRequiredMixin

from .models import SalesTarget, Expense
from .forms import SalesTargetForm, ExpenseForm
from .services import SalesAnalyticsService


class SalesBaseMixin(LoginRequiredMixin, ModulePermissionMixin):
    """Base mixin for Sales views with tenant filtering and module permission."""

    module_required = "sales"

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

    def form_valid(self, form):
        """Set organization on save."""
        org = self.get_organization()
        if org and hasattr(form, 'instance'):
            form.instance.organization = org
        return super().form_valid(form)


class SalesDashboardView(SalesBaseMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard principal des ventes avec KPIs."""
    template_name = 'sales/dashboard.html'
    permission_required = "sales_view"

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

        # Currency symbol (default to FCFA)
        context['currency_symbol'] = 'FCFA'

        # Get revenue stats (paid invoices only)
        context['revenue_ytd'] = SalesAnalyticsService.get_revenue_stats(
            org, year_start, today, paid_only=True
        )
        context['revenue_mtd'] = SalesAnalyticsService.get_revenue_stats(
            org, month_start, today, paid_only=True
        )

        # Get expenses
        expenses_mtd = Expense.objects.filter(
            organization=org,
            date__gte=month_start,
            date__lte=today
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        context['expenses_mtd'] = {
            'total': expenses_mtd['total'] or Decimal('0'),
            'count': expenses_mtd['count'] or 0
        }

        # Monthly profit
        revenue = context['revenue_mtd'].get('total_revenue', 0) or Decimal('0')
        expenses = context['expenses_mtd']['total']
        context['monthly_profit'] = revenue - expenses

        # Expenses by category
        category_display = dict(Expense.CATEGORY_CHOICES)
        expenses_by_cat = Expense.objects.filter(
            organization=org,
            date__gte=month_start,
            date__lte=today
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')[:5]

        context['expenses_by_category'] = [
            {
                'category': item['category'],
                'category_display': category_display.get(item['category'], item['category']),
                'total': item['total']
            }
            for item in expenses_by_cat
        ]

        context['overdue'] = SalesAnalyticsService.get_overdue_summary(org)
        context['top_clients'] = SalesAnalyticsService.get_top_clients(
            org, year_start, today, limit=5, paid_only=True
        )

        # Comparison with previous period (month)
        context['comparison'] = SalesAnalyticsService.get_comparison_period(
            org, month_start, today, paid_only=True
        )

        context['current_year'] = today.year
        context['current_month'] = today.month

        return context


class RevenueChartAPIView(SalesBaseMixin, TemplateView):
    """API endpoint for revenue chart data."""
    template_name = 'sales/dashboard.html'

    def get(self, request, *args, **kwargs):
        org = self.get_organization()
        if not org:
            return JsonResponse({'error': 'No organization'}, status=400)

        year = request.GET.get('year', timezone.now().year)
        try:
            year = int(year)
        except ValueError:
            year = timezone.now().year

        monthly_data = SalesAnalyticsService.get_monthly_revenue(org, year, paid_only=True)

        labels = []
        revenue_data = []

        months_fr = [
            'Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Jun',
            'Jul', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec'
        ]

        for item in monthly_data:
            month_num = item['month'].month
            labels.append(months_fr[month_num - 1])
            revenue_data.append(float(item['revenue'] or 0))

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'CA (factures payees)',
                'data': revenue_data,
                'backgroundColor': 'rgba(37, 99, 235, 0.7)',
                'borderColor': 'rgb(37, 99, 235)',
                'borderWidth': 1,
            }]
        })


class ProfitChartAPIView(SalesBaseMixin, TemplateView):
    """API endpoint for profit chart (CA vs Expenses)."""
    template_name = 'sales/dashboard.html'

    def get(self, request, *args, **kwargs):
        org = self.get_organization()
        if not org:
            return JsonResponse({'error': 'No organization'}, status=400)

        year = timezone.now().year
        monthly_revenue = SalesAnalyticsService.get_monthly_revenue(org, year, paid_only=True)

        # Get monthly expenses
        from django.db.models.functions import TruncMonth
        monthly_expenses = Expense.objects.filter(
            organization=org,
            date__year=year
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')

        expenses_dict = {item['month']: float(item['total']) for item in monthly_expenses}

        labels = []
        revenue_data = []
        expense_data = []

        months_fr = [
            'Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Jun',
            'Jul', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec'
        ]

        for item in monthly_revenue:
            month_date = item['month']
            labels.append(months_fr[month_date.month - 1])
            revenue_data.append(float(item['revenue'] or 0))
            expense_data.append(expenses_dict.get(month_date, 0))

        return JsonResponse({
            'labels': labels,
            'datasets': [
                {
                    'label': 'Chiffre d\'affaires',
                    'data': revenue_data,
                    'borderColor': 'rgb(16, 185, 129)',
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'tension': 0.3,
                    'fill': True,
                },
                {
                    'label': 'Depenses',
                    'data': expense_data,
                    'borderColor': 'rgb(239, 68, 68)',
                    'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                    'tension': 0.3,
                    'fill': True,
                }
            ]
        })


# ============================================================================
# Expense Views
# ============================================================================

class ExpenseListView(SalesBaseMixin, PermissionRequiredMixin, ListView):
    """Liste des depenses."""
    model = Expense
    template_name = 'sales/expense_list.html'
    context_object_name = 'expenses'
    permission_required = "sales_view"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()

        # Filters
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)

        month = self.request.GET.get('month')
        year = self.request.GET.get('year', timezone.now().year)
        if month:
            qs = qs.filter(date__month=month, date__year=year)
        elif year:
            qs = qs.filter(date__year=year)

        return qs.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()

        # Summary
        expenses = self.get_queryset()
        context['total_amount'] = expenses.aggregate(total=Sum('amount'))['total'] or 0
        context['expense_count'] = expenses.count()

        # Filters data
        context['categories'] = Expense.CATEGORY_CHOICES
        context['current_category'] = self.request.GET.get('category', '')
        context['current_year'] = int(self.request.GET.get('year', timezone.now().year))
        context['current_month'] = self.request.GET.get('month', '')
        context['years'] = range(timezone.now().year - 2, timezone.now().year + 1)

        return context


class ExpenseCreateView(SalesBaseMixin, PermissionRequiredMixin, CreateView):
    """Creation d'une depense."""
    model = Expense
    form_class = ExpenseForm
    template_name = 'sales/expense_form.html'
    success_url = reverse_lazy('sales:expense_list')
    permission_required = "sales_create"

    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Depense ajoutee avec succes.')
        return super().form_valid(form)


class ExpenseUpdateView(SalesBaseMixin, PermissionRequiredMixin, UpdateView):
    """Modification d'une depense."""
    model = Expense
    form_class = ExpenseForm
    template_name = 'sales/expense_form.html'
    success_url = reverse_lazy('sales:expense_list')
    permission_required = "sales_edit"

    def form_valid(self, form):
        messages.success(self.request, 'Depense modifiee avec succes.')
        return super().form_valid(form)


class ExpenseDeleteView(SalesBaseMixin, PermissionRequiredMixin, DeleteView):
    """Suppression d'une depense."""
    model = Expense
    template_name = 'sales/expense_confirm_delete.html'
    success_url = reverse_lazy('sales:expense_list')
    permission_required = "sales_delete"

    def post(self, request, *args, **kwargs):
        messages.success(self.request, 'Depense supprimee.')
        return super().post(request, *args, **kwargs)


# ============================================================================
# Sales Target Views
# ============================================================================

class SalesTargetListView(SalesBaseMixin, PermissionRequiredMixin, ListView):
    """Liste des objectifs de vente."""
    model = SalesTarget
    template_name = 'sales/target_list.html'
    context_object_name = 'targets'
    permission_required = "sales_view"

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


class SalesTargetDetailView(SalesBaseMixin, PermissionRequiredMixin, DetailView):
    """Detail d'un objectif de vente avec suivi de progression."""
    model = SalesTarget
    template_name = 'sales/target_detail.html'
    context_object_name = 'target'
    permission_required = "sales_view"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        target = self.object

        # Calculate current progress
        if target.target_type == 'revenue':
            stats = SalesAnalyticsService.get_revenue_stats(
                org, target.start_date, target.end_date, paid_only=True
            )
            context['current_value'] = stats.get('total_revenue', 0)
        elif target.target_type == 'invoices':
            stats = SalesAnalyticsService.get_revenue_stats(
                org, target.start_date, target.end_date, paid_only=True
            )
            context['current_value'] = stats.get('invoice_count', 0)
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


class SalesTargetCreateView(SalesBaseMixin, PermissionRequiredMixin, CreateView):
    """Creation d'un objectif de vente."""
    model = SalesTarget
    form_class = SalesTargetForm
    template_name = 'sales/target_form.html'
    success_url = reverse_lazy('sales:target_list')
    permission_required = "sales_create"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        messages.success(self.request, 'Objectif cree avec succes.')
        return super().form_valid(form)


class SalesTargetUpdateView(SalesBaseMixin, PermissionRequiredMixin, UpdateView):
    """Modification d'un objectif de vente."""
    model = SalesTarget
    form_class = SalesTargetForm
    template_name = 'sales/target_form.html'
    success_url = reverse_lazy('sales:target_list')
    permission_required = "sales_edit"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Objectif modifie avec succes.')
        return super().form_valid(form)


class SalesTargetDeleteView(SalesBaseMixin, PermissionRequiredMixin, DeleteView):
    """Suppression d'un objectif de vente."""
    model = SalesTarget
    template_name = 'sales/target_confirm_delete.html'
    success_url = reverse_lazy('sales:target_list')
    permission_required = "sales_delete"

    def post(self, request, *args, **kwargs):
        messages.success(self.request, 'Objectif supprime.')
        return super().post(request, *args, **kwargs)
