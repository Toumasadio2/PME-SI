from django.urls import path
from . import views

app_name = 'invoicing'

urlpatterns = [
    # Dashboard
    path('', views.InvoicingDashboardView.as_view(), name='dashboard'),

    # Products
    path('produits/', views.ProductListView.as_view(), name='product_list'),
    path('produits/nouveau/', views.ProductCreateView.as_view(), name='product_create'),
    path('produits/<int:pk>/modifier/', views.ProductUpdateView.as_view(), name='product_update'),
    path('produits/<int:pk>/supprimer/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('api/produits/<int:pk>/', views.product_info_api, name='product_info_api'),

    # Product Categories
    path('categories/', views.ProductCategoryListView.as_view(), name='category_list'),
    path('categories/nouvelle/', views.ProductCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/modifier/', views.ProductCategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/supprimer/', views.ProductCategoryDeleteView.as_view(), name='category_delete'),

    # Product Tags
    path('tags/', views.ProductTagListView.as_view(), name='tag_list'),
    path('tags/nouveau/', views.ProductTagCreateView.as_view(), name='tag_create'),
    path('tags/<int:pk>/modifier/', views.ProductTagUpdateView.as_view(), name='tag_update'),
    path('tags/<int:pk>/supprimer/', views.ProductTagDeleteView.as_view(), name='tag_delete'),

    # Quotes
    path('devis/', views.QuoteListView.as_view(), name='quote_list'),
    path('devis/nouveau/', views.QuoteCreateView.as_view(), name='quote_create'),
    path('devis/<int:pk>/', views.QuoteDetailView.as_view(), name='quote_detail'),
    path('devis/<int:pk>/modifier/', views.QuoteUpdateView.as_view(), name='quote_update'),
    path('devis/<int:pk>/supprimer/', views.QuoteDeleteView.as_view(), name='quote_delete'),
    path('devis/<int:pk>/statut/', views.quote_change_status, name='quote_change_status'),
    path('devis/<int:pk>/convertir/', views.quote_convert_to_invoice, name='quote_convert'),
    path('devis/<int:pk>/pdf/', views.quote_pdf, name='quote_pdf'),
    path('devis/<int:pk>/pdf/apercu/', views.quote_pdf_view, name='quote_pdf_view'),
    path('devis/<int:pk>/envoyer/', views.QuoteSendEmailView.as_view(), name='quote_send_email'),

    # Invoices
    path('factures/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('factures/nouvelle/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('factures/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('factures/<int:pk>/modifier/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('factures/<int:pk>/supprimer/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('factures/<int:pk>/statut/', views.invoice_change_status, name='invoice_change_status'),
    path('factures/<int:pk>/paiement/', views.invoice_add_payment, name='invoice_add_payment'),
    path('factures/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('factures/<int:pk>/pdf/apercu/', views.invoice_pdf_view, name='invoice_pdf_view'),
    path('factures/<int:pk>/envoyer/', views.InvoiceSendEmailView.as_view(), name='invoice_send_email'),
    path('factures/<int:pk>/relance/', views.InvoiceSendReminderView.as_view(), name='invoice_send_reminder'),
]
