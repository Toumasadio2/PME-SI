from django.contrib import admin
from .models import Product, Quote, QuoteItem, Invoice, InvoiceItem, Payment


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1
    fields = ['description', 'quantity', 'unit', 'unit_price', 'vat_rate', 'discount_percent', 'position']


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['description', 'quantity', 'unit', 'unit_price', 'vat_rate', 'discount_percent', 'position']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['amount', 'payment_date', 'method', 'reference']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['reference', 'name', 'product_type', 'unit_price', 'vat_rate', 'is_active', 'organization']
    list_filter = ['product_type', 'is_active', 'organization']
    search_fields = ['reference', 'name', 'description']
    ordering = ['name']


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['number', 'company', 'subject', 'status', 'total_ttc', 'issue_date', 'expiry_date']
    list_filter = ['status', 'organization', 'issue_date']
    search_fields = ['number', 'company__name', 'subject']
    date_hierarchy = 'issue_date'
    inlines = [QuoteItemInline]
    readonly_fields = ['total_ht', 'total_vat', 'total_ttc']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['number', 'company', 'subject', 'status', 'total_ttc', 'amount_paid', 'issue_date', 'due_date']
    list_filter = ['status', 'organization', 'issue_date']
    search_fields = ['number', 'company__name', 'subject']
    date_hierarchy = 'issue_date'
    inlines = [InvoiceItemInline, PaymentInline]
    readonly_fields = ['total_ht', 'total_vat', 'total_ttc', 'amount_paid']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_date', 'method', 'reference']
    list_filter = ['method', 'payment_date']
    search_fields = ['invoice__number', 'reference']
    date_hierarchy = 'payment_date'
