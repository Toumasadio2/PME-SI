from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory

from apps.crm.models import Company, Contact
from .models import Product, ProductCategory, ProductTag, Quote, QuoteItem, Invoice, InvoiceItem, Payment


class ProductForm(forms.ModelForm):
    """Formulaire pour les produits/services."""

    class Meta:
        model = Product
        fields = [
            'reference', 'name', 'description', 'product_type', 'image',
            'category', 'tags',
            'unit_price', 'vat_rate', 'unit',
            'track_stock', 'stock_quantity', 'stock_alert_threshold', 'stock_status',
            'is_active'
        ]
        widgets = {
            'reference': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'REF-001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom du produit ou service'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Description détaillée...'
            }),
            'product_type': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '4'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0'
            }),
            'vat_rate': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'unité, heure, jour...'
            }),
            'track_stock': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0'
            }),
            'stock_alert_threshold': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0'
            }),
            'stock_status': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['category'].queryset = ProductCategory.objects.filter(
                organization=organization, is_active=True
            )
            self.fields['tags'].queryset = ProductTag.objects.filter(
                organization=organization
            )
        self.fields['category'].required = False
        self.fields['tags'].required = False
        self.fields['image'].required = False

    def clean_image(self):
        """Valide l'image uploadée."""
        image = self.cleaned_data.get('image')
        if image:
            # Vérifie la taille (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('L\'image ne doit pas dépasser 5 Mo.')
            # Vérifie le type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise forms.ValidationError('Format d\'image non supporté. Utilisez JPG, PNG, GIF ou WebP.')
        return image


class QuoteForm(forms.ModelForm):
    """Formulaire pour les devis."""

    CLIENT_TYPE_CHOICES = [
        ('company', 'Entreprise'),
        ('individual', 'Particulier'),
    ]

    client_type = forms.ChoiceField(
        choices=CLIENT_TYPE_CHOICES,
        initial='company',
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )

    class Meta:
        model = Quote
        fields = [
            'company', 'contact', 'subject', 'introduction',
            'conditions', 'validity_days', 'issue_date',
            'client_name', 'client_email', 'client_phone', 'client_address'
        ]
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'contact': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Objet du devis'
            }),
            'introduction': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Introduction du devis...'
            }),
            'conditions': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Conditions particulières...'
            }),
            'validity_days': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1'
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'client_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom complet du client'
            }),
            'client_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'email@exemple.com'
            }),
            'client_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+33 6 12 34 56 78'
            }),
            'client_address': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 2,
                'placeholder': 'Adresse complète'
            }),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['company'].queryset = Company.objects.filter(
                organization=organization
            )
            self.fields['contact'].queryset = Contact.objects.filter(
                organization=organization
            )
        # Rendre tous les champs client optionnels
        self.fields['company'].required = False
        self.fields['contact'].required = False
        self.fields['client_name'].required = False
        self.fields['client_email'].required = False
        self.fields['client_phone'].required = False
        self.fields['client_address'].required = False

    def clean(self):
        cleaned_data = super().clean()
        client_type = cleaned_data.get('client_type')
        company = cleaned_data.get('company')
        client_name = cleaned_data.get('client_name')

        if client_type == 'company' and not company:
            self.add_error('company', 'Veuillez sélectionner une entreprise.')
        elif client_type == 'individual' and not client_name:
            self.add_error('client_name', 'Veuillez saisir le nom du client.')

        return cleaned_data


class QuoteItemForm(forms.ModelForm):
    """Formulaire pour les lignes de devis."""

    class Meta:
        model = QuoteItem
        fields = [
            'product', 'description', 'quantity', 'unit',
            'unit_price', 'vat_rate', 'discount_percent'
        ]
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select item-product',
                'hx-get': '',
                'hx-trigger': 'change',
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input item-quantity',
                'step': '0.01',
                'min': '0.01',
                'value': '1'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'unité'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-input item-price',
                'step': '0.01',
                'min': '0'
            }),
            'vat_rate': forms.NumberInput(attrs={
                'class': 'form-input item-vat',
                'step': '0.01',
                'value': '20.00'
            }),
            'discount_percent': forms.NumberInput(attrs={
                'class': 'form-input item-discount',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0'
            }),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['product'].queryset = Product.objects.filter(
                organization=organization,
                is_active=True
            )
        self.fields['product'].required = False


QuoteItemFormSet = inlineformset_factory(
    Quote,
    QuoteItem,
    form=QuoteItemForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)


class InvoiceForm(forms.ModelForm):
    """Formulaire pour les factures."""

    CLIENT_TYPE_CHOICES = [
        ('company', 'Entreprise'),
        ('individual', 'Particulier'),
    ]

    client_type = forms.ChoiceField(
        choices=CLIENT_TYPE_CHOICES,
        initial='company',
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )

    class Meta:
        model = Invoice
        fields = [
            'company', 'contact', 'subject', 'introduction',
            'conditions', 'legal_mentions', 'payment_terms_days', 'issue_date',
            'client_name', 'client_email', 'client_phone', 'client_address'
        ]
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'contact': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Objet de la facture'
            }),
            'introduction': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Introduction...'
            }),
            'conditions': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 2,
                'placeholder': 'Conditions de paiement...'
            }),
            'legal_mentions': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Mentions légales obligatoires...'
            }),
            'payment_terms_days': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0'
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'client_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom complet du client'
            }),
            'client_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'email@exemple.com'
            }),
            'client_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+33 6 12 34 56 78'
            }),
            'client_address': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 2,
                'placeholder': 'Adresse complète'
            }),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['company'].queryset = Company.objects.filter(
                organization=organization
            )
            self.fields['contact'].queryset = Contact.objects.filter(
                organization=organization
            )
        # Rendre tous les champs client optionnels
        self.fields['company'].required = False
        self.fields['contact'].required = False
        self.fields['client_name'].required = False
        self.fields['client_email'].required = False
        self.fields['client_phone'].required = False
        self.fields['client_address'].required = False

    def clean(self):
        cleaned_data = super().clean()
        client_type = cleaned_data.get('client_type')
        company = cleaned_data.get('company')
        client_name = cleaned_data.get('client_name')

        if client_type == 'company' and not company:
            self.add_error('company', 'Veuillez sélectionner une entreprise.')
        elif client_type == 'individual' and not client_name:
            self.add_error('client_name', 'Veuillez saisir le nom du client.')

        return cleaned_data


class InvoiceItemForm(forms.ModelForm):
    """Formulaire pour les lignes de facture."""

    class Meta:
        model = InvoiceItem
        fields = [
            'product', 'description', 'quantity', 'unit',
            'unit_price', 'vat_rate', 'discount_percent'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select item-product'}),
            'description': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input item-quantity',
                'step': '0.01',
                'min': '0.01',
                'value': '1'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'unité'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-input item-price',
                'step': '0.01',
                'min': '0'
            }),
            'vat_rate': forms.NumberInput(attrs={
                'class': 'form-input item-vat',
                'step': '0.01',
                'value': '20.00'
            }),
            'discount_percent': forms.NumberInput(attrs={
                'class': 'form-input item-discount',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0'
            }),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['product'].queryset = Product.objects.filter(
                organization=organization,
                is_active=True
            )
        self.fields['product'].required = False


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)


class PaymentForm(forms.ModelForm):
    """Formulaire pour enregistrer un paiement."""

    class Meta:
        model = Payment
        fields = ['amount', 'payment_date', 'method', 'reference', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0.01'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Numéro de chèque, référence virement...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 2,
                'placeholder': 'Notes sur le paiement...'
            }),
        }


class QuoteStatusForm(forms.Form):
    """Formulaire pour changer le statut d'un devis."""
    status = forms.ChoiceField(
        choices=Quote.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class InvoiceStatusForm(forms.Form):
    """Formulaire pour changer le statut d'une facture."""
    status = forms.ChoiceField(
        choices=Invoice.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ProductCategoryForm(forms.ModelForm):
    """Formulaire pour les catégories de produits."""

    class Meta:
        model = ProductCategory
        fields = ['name', 'slug', 'description', 'parent', 'color', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom de la catégorie'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'nom-categorie'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 2,
                'placeholder': 'Description de la catégorie...'
            }),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['parent'].queryset = ProductCategory.objects.filter(
                organization=organization
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
        self.fields['parent'].required = False


class ProductTagForm(forms.ModelForm):
    """Formulaire pour les tags de produits."""

    class Meta:
        model = ProductTag
        fields = ['name', 'slug', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom du tag'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'nom-tag'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color'
            }),
        }


class ProductSearchForm(forms.Form):
    """Formulaire de recherche de produits."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Rechercher...'
        })
    )
    product_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous types')] + Product.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=ProductCategory.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Toutes catégories'
    )
    stock_status = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous statuts')] + Product.STOCK_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous'), ('true', 'Actifs'), ('false', 'Inactifs')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['category'].queryset = ProductCategory.objects.filter(
                organization=organization, is_active=True
            )


class SendEmailForm(forms.Form):
    """Formulaire pour l'envoi d'email."""
    recipient_email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'destinataire@email.com'
        })
    )
    message = forms.CharField(
        label='Message personnalisé (optionnel)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 4,
            'placeholder': 'Ajoutez un message personnalisé qui accompagnera le document...'
        })
    )
