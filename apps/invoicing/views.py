"""Invoicing Views."""
import json
from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.utils import timezone

from .models import Product, ProductCategory, ProductTag, Quote, QuoteItem, Invoice, InvoiceItem, Payment
from .forms import (
    ProductForm, ProductCategoryForm, ProductTagForm, QuoteForm, QuoteItemFormSet, InvoiceForm,
    InvoiceItemFormSet, PaymentForm, ProductSearchForm, SendEmailForm
)
from .emails import EmailService
from .services import NumberingService, QuoteService
from .pdf import PDFService, PDFGenerationError


class InvoicingBaseMixin(LoginRequiredMixin):
    """Base mixin for Invoicing views with tenant filtering."""

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
        if org:
            form.instance.organization = org
        return super().form_valid(form)


# =============================================================================
# Dashboard
# =============================================================================

class InvoicingDashboardView(InvoicingBaseMixin, TemplateView):
    """Dashboard du module facturation."""
    template_name = 'invoicing/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()

        if not org:
            context['stats'] = {
                'revenue_year': 0,
                'revenue_month': 0,
                'unpaid_total': 0,
                'overdue_count': 0,
                'invoices_count': 0,
                'quotes_pending': 0,
            }
            context['recent_invoices'] = []
            context['recent_quotes'] = []
            context['overdue_invoices'] = []
            return context

        today = timezone.now().date()
        current_year = today.year
        current_month = today.month

        # Invoices stats (exclude soft-deleted)
        invoices = Invoice.objects.filter(organization=org, is_deleted=False)
        invoices_this_year = invoices.filter(issue_date__year=current_year)
        invoices_this_month = invoices.filter(
            issue_date__year=current_year,
            issue_date__month=current_month
        )

        # Revenue calculations
        paid_invoices = invoices_this_year.filter(status='paid')
        unpaid_invoices = invoices_this_year.filter(
            status__in=['sent', 'partial', 'overdue']
        )

        context['stats'] = {
            'revenue_year': sum(inv.total_ttc for inv in paid_invoices),
            'revenue_month': sum(
                inv.total_ttc for inv in paid_invoices.filter(
                    issue_date__month=current_month
                )
            ),
            'unpaid_total': sum(inv.balance_due for inv in unpaid_invoices),
            'overdue_count': invoices.filter(status='overdue').count(),
            'invoices_count': invoices_this_month.count(),
            'quotes_pending': Quote.objects.filter(
                organization=org,
                status__in=['draft', 'sent']
            ).count(),
        }

        # Recent invoices (exclude soft-deleted)
        context['recent_invoices'] = Invoice.objects.filter(
            organization=org, is_deleted=False
        ).order_by('-created_at')[:5]

        # Recent quotes
        context['recent_quotes'] = Quote.objects.filter(
            organization=org
        ).order_by('-created_at')[:5]

        # Overdue invoices (exclude soft-deleted)
        context['overdue_invoices'] = Invoice.objects.filter(
            organization=org,
            status='overdue',
            is_deleted=False
        ).order_by('due_date')[:5]

        # Chart data: Monthly revenue for the last 12 months
        monthly_revenue = []
        for i in range(11, -1, -1):
            month_date = today - relativedelta(months=i)
            month_invoices = Invoice.objects.filter(
                organization=org,
                status='paid',
                is_deleted=False,
                issue_date__year=month_date.year,
                issue_date__month=month_date.month
            )
            revenue = sum(inv.total_ttc for inv in month_invoices)
            monthly_revenue.append({
                'month': month_date.strftime('%b %Y'),
                'revenue': float(revenue)
            })
        context['monthly_revenue_json'] = json.dumps(monthly_revenue)

        # Chart data: Invoice status distribution
        status_counts = {}
        for status_code, status_label in Invoice.STATUS_CHOICES:
            count = invoices_this_year.filter(status=status_code).count()
            if count > 0:
                status_counts[status_label] = count
        context['invoice_status_json'] = json.dumps(status_counts)

        # Chart data: Quotes status distribution
        quotes_this_year = Quote.objects.filter(
            organization=org,
            issue_date__year=current_year
        )
        quote_status_counts = {}
        for status_code, status_label in Quote.STATUS_CHOICES:
            count = quotes_this_year.filter(status=status_code).count()
            if count > 0:
                quote_status_counts[status_label] = count
        context['quote_status_json'] = json.dumps(quote_status_counts)

        return context


# =============================================================================
# Products
# =============================================================================

class ProductListView(InvoicingBaseMixin, ListView):
    """Liste des produits/services."""
    model = Product
    template_name = 'invoicing/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category').prefetch_related('tags')

        # Search
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(reference__icontains=q) |
                Q(name__icontains=q) |
                Q(description__icontains=q)
            )

        # Filter by type
        product_type = self.request.GET.get('product_type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)

        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        # Filter by tag
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__id=tag)

        # Filter by active status
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        # Filter by stock status
        stock_status = self.request.GET.get('stock_status')
        if stock_status:
            queryset = queryset.filter(stock_status=stock_status)

        return queryset.order_by('name').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        context['search_form'] = ProductSearchForm(self.request.GET, organization=org)
        context['total_count'] = self.get_queryset().count()
        context['categories'] = ProductCategory.objects.filter(
            organization=org, is_active=True
        ) if org else ProductCategory.objects.none()
        context['tags'] = ProductTag.objects.filter(
            organization=org
        ) if org else ProductTag.objects.none()
        return context


class ProductCreateView(InvoicingBaseMixin, CreateView):
    """Création d'un produit."""
    model = Product
    form_class = ProductForm
    template_name = 'invoicing/product_form.html'
    success_url = reverse_lazy('invoicing:product_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Produit créé avec succès.')
        return super().form_valid(form)


class ProductUpdateView(InvoicingBaseMixin, UpdateView):
    """Modification d'un produit."""
    model = Product
    form_class = ProductForm
    template_name = 'invoicing/product_form.html'
    success_url = reverse_lazy('invoicing:product_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Produit modifié avec succès.')
        return super().form_valid(form)


class ProductDeleteView(InvoicingBaseMixin, DeleteView):
    """Suppression d'un produit."""
    model = Product
    template_name = 'invoicing/product_confirm_delete.html'
    success_url = reverse_lazy('invoicing:product_list')

    def form_valid(self, form):
        """Handle successful form submission (Django 4.x+)."""
        messages.success(self.request, 'Produit supprimé avec succès.')
        return super().form_valid(form)


# =============================================================================
# Product Categories
# =============================================================================

class ProductCategoryListView(InvoicingBaseMixin, ListView):
    """Liste des catégories de produits."""
    model = ProductCategory
    template_name = 'invoicing/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return super().get_queryset().filter(parent__isnull=True).prefetch_related('children')


class ProductCategoryCreateView(InvoicingBaseMixin, CreateView):
    """Création d'une catégorie de produit."""
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'invoicing/category_form.html'
    success_url = reverse_lazy('invoicing:category_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Catégorie créée avec succès.')
        return super().form_valid(form)


class ProductCategoryUpdateView(InvoicingBaseMixin, UpdateView):
    """Modification d'une catégorie de produit."""
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'invoicing/category_form.html'
    success_url = reverse_lazy('invoicing:category_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Catégorie modifiée avec succès.')
        return super().form_valid(form)


class ProductCategoryDeleteView(InvoicingBaseMixin, DeleteView):
    """Suppression d'une catégorie de produit."""
    model = ProductCategory
    template_name = 'invoicing/category_confirm_delete.html'
    success_url = reverse_lazy('invoicing:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Catégorie supprimée avec succès.')
        return super().form_valid(form)


# =============================================================================
# Product Tags
# =============================================================================

class ProductTagListView(InvoicingBaseMixin, ListView):
    """Liste des tags de produits."""
    model = ProductTag
    template_name = 'invoicing/tag_list.html'
    context_object_name = 'tags'


class ProductTagCreateView(InvoicingBaseMixin, CreateView):
    """Création d'un tag de produit."""
    model = ProductTag
    form_class = ProductTagForm
    template_name = 'invoicing/tag_form.html'
    success_url = reverse_lazy('invoicing:tag_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tag créé avec succès.')
        return super().form_valid(form)


class ProductTagUpdateView(InvoicingBaseMixin, UpdateView):
    """Modification d'un tag de produit."""
    model = ProductTag
    form_class = ProductTagForm
    template_name = 'invoicing/tag_form.html'
    success_url = reverse_lazy('invoicing:tag_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tag modifié avec succès.')
        return super().form_valid(form)


class ProductTagDeleteView(InvoicingBaseMixin, DeleteView):
    """Suppression d'un tag de produit."""
    model = ProductTag
    template_name = 'invoicing/tag_confirm_delete.html'
    success_url = reverse_lazy('invoicing:tag_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tag supprimé avec succès.')
        return super().form_valid(form)


# =============================================================================
# Quotes
# =============================================================================

class QuoteListView(InvoicingBaseMixin, ListView):
    """Liste des devis."""
    model = Quote
    template_name = 'invoicing/quote_list.html'
    context_object_name = 'quotes'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('company', 'contact')

        # Search
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(number__icontains=q) |
                Q(subject__icontains=q) |
                Q(company__name__icontains=q) |
                Q(client_name__icontains=q)
            )

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-issue_date', '-number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = self.get_queryset().count()
        context['status_choices'] = Quote.STATUS_CHOICES
        return context


class QuoteDetailView(InvoicingBaseMixin, DetailView):
    """Détail d'un devis."""
    model = Quote
    template_name = 'invoicing/quote_detail.html'
    context_object_name = 'quote'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'company', 'contact'
        ).prefetch_related('items')


class QuoteCreateView(InvoicingBaseMixin, CreateView):
    """Création d'un devis."""
    model = Quote
    form_class = QuoteForm
    template_name = 'invoicing/quote_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        if self.request.POST:
            context['items_formset'] = QuoteItemFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['items_formset'] = QuoteItemFormSet(instance=self.object)

        # Set organization for each item form
        for form in context['items_formset'].forms:
            form.fields['product'].queryset = Product.objects.filter(
                organization=org, is_active=True
            ) if org else Product.objects.none()

        context['products'] = Product.objects.filter(
            organization=org, is_active=True
        ) if org else Product.objects.none()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']

        org = self.get_organization()
        form.instance.organization = org
        form.instance.number = NumberingService.generate_quote_number(org)
        form.instance.created_by = self.request.user

        self.object = form.save()

        if items_formset.is_valid():
            items_formset.instance = self.object
            items_formset.save()
            self.object.calculate_totals()
            messages.success(self.request, f'Devis {self.object.number} créé avec succès.')
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(context)


class QuoteUpdateView(InvoicingBaseMixin, UpdateView):
    """Modification d'un devis."""
    model = Quote
    form_class = QuoteForm
    template_name = 'invoicing/quote_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        if self.request.POST:
            context['items_formset'] = QuoteItemFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['items_formset'] = QuoteItemFormSet(instance=self.object)

        for form in context['items_formset'].forms:
            form.fields['product'].queryset = Product.objects.filter(
                organization=org, is_active=True
            ) if org else Product.objects.none()

        context['products'] = Product.objects.filter(
            organization=org, is_active=True
        ) if org else Product.objects.none()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']

        self.object = form.save()

        if items_formset.is_valid():
            items_formset.save()
            self.object.calculate_totals()
            messages.success(self.request, 'Devis modifié avec succès.')
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(context)


class QuoteDeleteView(InvoicingBaseMixin, DeleteView):
    """Suppression d'un devis."""
    model = Quote
    template_name = 'invoicing/quote_confirm_delete.html'
    success_url = reverse_lazy('invoicing:quote_list')

    def form_valid(self, form):
        """Handle successful form submission (Django 4.x+)."""
        quote = self.get_object()
        messages.success(self.request, f'Devis {quote.number} supprimé.')
        return super().form_valid(form)


@login_required
def quote_change_status(request, pk):
    """Change le statut d'un devis."""
    org = getattr(request, 'organization', None)
    quote = get_object_or_404(Quote, pk=pk, organization=org)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Quote.STATUS_CHOICES):
            quote.status = new_status
            quote.save(update_fields=['status'])
            messages.success(request, 'Statut du devis mis à jour.')
    return redirect(quote.get_absolute_url())


@login_required
def quote_convert_to_invoice(request, pk):
    """Convertit un devis accepté en facture."""
    org = getattr(request, 'organization', None)
    quote = get_object_or_404(Quote, pk=pk, organization=org)

    if not quote.can_convert_to_invoice():
        messages.error(request, 'Ce devis ne peut pas être converti en facture.')
        return redirect(quote.get_absolute_url())

    try:
        invoice = QuoteService.convert_to_invoice(quote, created_by=request.user)
        messages.success(
            request,
            f'Facture {invoice.number} créée à partir du devis {quote.number}.'
        )
        return redirect(invoice.get_absolute_url())
    except ValueError as e:
        messages.error(request, str(e))
        return redirect(quote.get_absolute_url())


# =============================================================================
# Invoices
# =============================================================================

class InvoiceListView(InvoicingBaseMixin, ListView):
    """Liste des factures."""
    model = Invoice
    template_name = 'invoicing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('company', 'contact')

        # Exclude soft-deleted invoices
        queryset = queryset.filter(is_deleted=False)

        # Search
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(number__icontains=q) |
                Q(subject__icontains=q) |
                Q(company__name__icontains=q) |
                Q(client_name__icontains=q)
            )

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-issue_date', '-number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = self.get_queryset().count()
        context['status_choices'] = Invoice.STATUS_CHOICES
        return context


class InvoiceDetailView(InvoicingBaseMixin, DetailView):
    """Détail d'une facture."""
    model = Invoice
    template_name = 'invoicing/invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'company', 'contact', 'quote'
        ).prefetch_related('items', 'payments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_form'] = PaymentForm()
        return context


class InvoiceCreateView(InvoicingBaseMixin, CreateView):
    """Création d'une facture."""
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoicing/invoice_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        if self.request.POST:
            context['items_formset'] = InvoiceItemFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['items_formset'] = InvoiceItemFormSet(instance=self.object)

        for form in context['items_formset'].forms:
            form.fields['product'].queryset = Product.objects.filter(
                organization=org, is_active=True
            ) if org else Product.objects.none()

        context['products'] = Product.objects.filter(
            organization=org, is_active=True
        ) if org else Product.objects.none()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']

        org = self.get_organization()
        form.instance.organization = org
        form.instance.number = NumberingService.generate_invoice_number(org)
        form.instance.created_by = self.request.user

        self.object = form.save()

        if items_formset.is_valid():
            items_formset.instance = self.object
            items_formset.save()
            self.object.calculate_totals()
            messages.success(self.request, f'Facture {self.object.number} créée avec succès.')
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(context)


class InvoiceUpdateView(InvoicingBaseMixin, UpdateView):
    """Modification d'une facture."""
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoicing/invoice_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        if self.request.POST:
            context['items_formset'] = InvoiceItemFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['items_formset'] = InvoiceItemFormSet(instance=self.object)

        for form in context['items_formset'].forms:
            form.fields['product'].queryset = Product.objects.filter(
                organization=org, is_active=True
            ) if org else Product.objects.none()

        context['products'] = Product.objects.filter(
            organization=org, is_active=True
        ) if org else Product.objects.none()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']

        self.object = form.save()

        if items_formset.is_valid():
            items_formset.save()
            self.object.calculate_totals()
            messages.success(self.request, 'Facture modifiée avec succès.')
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(context)


class InvoiceDeleteView(InvoicingBaseMixin, DeleteView):
    """Suppression d'une facture (soft-delete)."""
    model = Invoice
    template_name = 'invoicing/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoicing:invoice_list')

    def get_queryset(self):
        # Exclude already deleted invoices
        return super().get_queryset().filter(is_deleted=False)

    def form_valid(self, form):
        """Handle successful form submission with soft-delete."""
        invoice = self.get_object()

        # Check if payments exist
        if invoice.payments.exists():
            messages.error(
                self.request,
                f'Impossible de supprimer la facture {invoice.number}: '
                f'des paiements sont enregistrés. Supprimez d\'abord les paiements.'
            )
            return redirect('invoicing:invoice_detail', pk=invoice.pk)

        # Perform soft-delete
        invoice.soft_delete(user=self.request.user)
        messages.success(self.request, f'Facture {invoice.number} supprimée.')
        return redirect(self.success_url)


@login_required
def invoice_change_status(request, pk):
    """Change le statut d'une facture."""
    org = getattr(request, 'organization', None)
    invoice = get_object_or_404(Invoice, pk=pk, organization=org)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Invoice.STATUS_CHOICES):
            invoice.status = new_status
            invoice.save(update_fields=['status'])
            messages.success(request, 'Statut de la facture mis à jour.')
    return redirect(invoice.get_absolute_url())


@login_required
def invoice_add_payment(request, pk):
    """Ajoute un paiement à une facture."""
    org = getattr(request, 'organization', None)
    invoice = get_object_or_404(Invoice, pk=pk, organization=org)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.created_by = request.user
            payment.save()
            messages.success(request, f'Paiement de {payment.amount}€ enregistré.')
        else:
            messages.error(request, 'Erreur lors de l\'enregistrement du paiement.')

    return redirect(invoice.get_absolute_url())


# =============================================================================
# API Endpoints (for HTMX/JS)
# =============================================================================

@login_required
def product_info_api(request, pk):
    """Retourne les infos d'un produit pour pré-remplir les lignes."""
    org = getattr(request, 'organization', None)
    product = get_object_or_404(Product, pk=pk, organization=org)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'description': product.name,
        'unit_price': str(product.unit_price),
        'vat_rate': str(product.vat_rate),
        'unit': product.unit,
    })


# =============================================================================
# PDF Downloads
# =============================================================================

@login_required
def quote_pdf(request, pk):
    """Télécharge le PDF d'un devis."""
    org = getattr(request, 'organization', None)
    quote = get_object_or_404(Quote, pk=pk, organization=org)

    try:
        pdf_bytes = PDFService.generate_quote_pdf(quote)
        filename = PDFService.get_quote_filename(quote)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except PDFGenerationError as e:
        messages.error(request, str(e))
        return redirect(quote.get_absolute_url())


@login_required
def quote_pdf_view(request, pk):
    """Affiche le PDF d'un devis dans le navigateur."""
    org = getattr(request, 'organization', None)
    quote = get_object_or_404(Quote, pk=pk, organization=org)

    try:
        pdf_bytes = PDFService.generate_quote_pdf(quote)
        filename = PDFService.get_quote_filename(quote)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except PDFGenerationError as e:
        messages.error(request, str(e))
        return redirect(quote.get_absolute_url())


@login_required
def invoice_pdf(request, pk):
    """Télécharge le PDF d'une facture."""
    org = getattr(request, 'organization', None)
    invoice = get_object_or_404(Invoice, pk=pk, organization=org)

    try:
        pdf_bytes = PDFService.generate_invoice_pdf(invoice)
        filename = PDFService.get_invoice_filename(invoice)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except PDFGenerationError as e:
        messages.error(request, str(e))
        return redirect(invoice.get_absolute_url())


@login_required
def invoice_pdf_view(request, pk):
    """Affiche le PDF d'une facture dans le navigateur."""
    org = getattr(request, 'organization', None)
    invoice = get_object_or_404(Invoice, pk=pk, organization=org)

    try:
        pdf_bytes = PDFService.generate_invoice_pdf(invoice)
        filename = PDFService.get_invoice_filename(invoice)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except PDFGenerationError as e:
        messages.error(request, str(e))
        return redirect(invoice.get_absolute_url())


# =============================================================================
# Email Sending
# =============================================================================

class QuoteSendEmailView(InvoicingBaseMixin, DetailView):
    """Formulaire d'envoi de devis par email."""
    model = Quote
    template_name = 'invoicing/quote_send_email.html'
    context_object_name = 'quote'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quote = self.object

        # Pre-fill recipient email
        initial_email = ''
        if quote.contact and quote.contact.email:
            initial_email = quote.contact.email
        elif quote.company and quote.company.email:
            initial_email = quote.company.email
        elif quote.client_email:
            initial_email = quote.client_email

        context['form'] = SendEmailForm(initial={'recipient_email': initial_email})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SendEmailForm(request.POST)

        if form.is_valid():
            try:
                EmailService.send_quote(
                    quote=self.object,
                    recipient_email=form.cleaned_data['recipient_email'],
                    message=form.cleaned_data.get('message')
                )
                messages.success(request, f'Devis envoyé à {form.cleaned_data["recipient_email"]}')
                return redirect(self.object.get_absolute_url())
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'envoi: {str(e)}')

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class InvoiceSendEmailView(InvoicingBaseMixin, DetailView):
    """Formulaire d'envoi de facture par email."""
    model = Invoice
    template_name = 'invoicing/invoice_send_email.html'
    context_object_name = 'invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = self.object

        # Pre-fill recipient email
        initial_email = ''
        if invoice.contact and invoice.contact.email:
            initial_email = invoice.contact.email
        elif invoice.company and invoice.company.email:
            initial_email = invoice.company.email
        elif invoice.client_email:
            initial_email = invoice.client_email

        context['form'] = SendEmailForm(initial={'recipient_email': initial_email})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SendEmailForm(request.POST)

        if form.is_valid():
            try:
                EmailService.send_invoice(
                    invoice=self.object,
                    recipient_email=form.cleaned_data['recipient_email'],
                    message=form.cleaned_data.get('message')
                )
                messages.success(request, f'Facture envoyée à {form.cleaned_data["recipient_email"]}')
                return redirect(self.object.get_absolute_url())
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'envoi: {str(e)}')

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class InvoiceSendReminderView(InvoicingBaseMixin, DetailView):
    """Formulaire d'envoi de relance par email."""
    model = Invoice
    template_name = 'invoicing/invoice_send_reminder.html'
    context_object_name = 'invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = self.object

        # Pre-fill recipient email
        initial_email = ''
        if invoice.contact and invoice.contact.email:
            initial_email = invoice.contact.email
        elif invoice.company and invoice.company.email:
            initial_email = invoice.company.email
        elif invoice.client_email:
            initial_email = invoice.client_email

        context['form'] = SendEmailForm(initial={'recipient_email': initial_email})
        context['reminder_number'] = invoice.reminder_count + 1
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SendEmailForm(request.POST)

        if form.is_valid():
            try:
                EmailService.send_reminder(
                    invoice=self.object,
                    recipient_email=form.cleaned_data['recipient_email'],
                    message=form.cleaned_data.get('message')
                )
                messages.success(request, f'Relance envoyée à {form.cleaned_data["recipient_email"]}')
                return redirect(self.object.get_absolute_url())
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'envoi: {str(e)}')

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)
