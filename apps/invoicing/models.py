from decimal import Decimal
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator

from apps.core.models import Organization
from apps.crm.models import Company, Contact


class ProductCategory(models.Model):
    """Catégorie de produit pour organisation et filtrage."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='product_categories'
    )
    name = models.CharField('Nom', max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField('Description', blank=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name='Catégorie parente'
    )
    color = models.CharField('Couleur', max_length=7, default='#6366f1')
    is_active = models.BooleanField('Actif', default=True)
    order = models.PositiveIntegerField('Ordre', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Catégorie de produit'
        verbose_name_plural = 'Catégories de produits'
        ordering = ['order', 'name']
        unique_together = [['organization', 'slug']]

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Retourne le chemin complet de la catégorie."""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name


class ProductTag(models.Model):
    """Tag pour les produits (étiquettes personnalisables)."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='product_tags'
    )
    name = models.CharField('Nom', max_length=50)
    slug = models.SlugField(max_length=50)
    color = models.CharField('Couleur', max_length=7, default='#10b981')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tag produit'
        verbose_name_plural = 'Tags produits'
        ordering = ['name']
        unique_together = [['organization', 'slug']]

    def __str__(self):
        return self.name


def product_image_path(instance, filename):
    """Génère le chemin de stockage pour les images produit."""
    import os
    ext = filename.split('.')[-1]
    new_filename = f"{instance.reference}.{ext}"
    return f"products/{instance.organization_id}/{new_filename}"


class Product(models.Model):
    """Produit ou service facturable."""

    TYPE_CHOICES = [
        ('product', 'Produit physique'),
        ('service', 'Service'),
        ('subscription', 'Abonnement'),
        ('digital', 'Produit numérique'),
    ]

    STOCK_STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('low_stock', 'Stock faible'),
        ('out_of_stock', 'Rupture de stock'),
        ('discontinued', 'Arrêté'),
        ('preorder', 'Précommande'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='products'
    )
    reference = models.CharField('Référence', max_length=50)
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    product_type = models.CharField(
        'Type',
        max_length=20,
        choices=TYPE_CHOICES,
        default='service'
    )

    # Image du produit
    image = models.ImageField(
        'Photo',
        upload_to=product_image_path,
        null=True,
        blank=True,
        help_text='Image du produit (JPG, PNG, max 5MB)'
    )

    # Catégorie et tags
    category = models.ForeignKey(
        ProductCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='products',
        verbose_name='Catégorie'
    )
    tags = models.ManyToManyField(
        ProductTag,
        blank=True,
        related_name='products',
        verbose_name='Tags'
    )

    unit_price = models.DecimalField(
        'Prix unitaire HT',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    vat_rate = models.DecimalField(
        'Taux TVA (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00')
    )
    unit = models.CharField('Unité', max_length=20, default='unité')

    # Gestion de stock (optionnel)
    track_stock = models.BooleanField('Suivre le stock', default=False)
    stock_quantity = models.IntegerField('Quantité en stock', default=0)
    stock_alert_threshold = models.IntegerField(
        'Seuil d\'alerte stock',
        default=10,
        help_text='Alerte quand le stock descend sous ce seuil'
    )
    stock_status = models.CharField(
        'Statut stock',
        max_length=20,
        choices=STOCK_STATUS_CHOICES,
        default='available',
        help_text='Statut de disponibilité du produit'
    )

    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['name']
        unique_together = ['organization', 'reference']

    def __str__(self):
        return f"{self.reference} - {self.name}"

    @property
    def stock_is_low(self):
        """Vérifie si le stock est sous le seuil d'alerte."""
        if not self.track_stock:
            return False
        return self.stock_quantity <= self.stock_alert_threshold

    @property
    def is_in_stock(self):
        """Vérifie si le produit est en stock."""
        if not self.track_stock:
            return True
        return self.stock_quantity > 0

    @property
    def is_available(self):
        """Vérifie si le produit est disponible à la vente."""
        if self.stock_status == 'discontinued':
            return False
        if not self.track_stock:
            return self.stock_status != 'out_of_stock'
        return self.stock_quantity > 0

    def update_stock_status(self):
        """Met à jour automatiquement le statut de stock selon la quantité."""
        if not self.track_stock:
            return

        if self.stock_quantity <= 0:
            self.stock_status = 'out_of_stock'
        elif self.stock_quantity <= self.stock_alert_threshold:
            self.stock_status = 'low_stock'
        else:
            self.stock_status = 'available'

    def adjust_stock(self, quantity_change, reason=''):
        """Ajuste le stock et met à jour le statut.

        Args:
            quantity_change: Positif pour ajouter, négatif pour retirer
            reason: Raison de l'ajustement (pour audit)
        """
        if not self.track_stock:
            return

        self.stock_quantity += quantity_change
        if self.stock_quantity < 0:
            self.stock_quantity = 0
        self.update_stock_status()
        self.save(update_fields=['stock_quantity', 'stock_status'])

    def get_stock_status_display_class(self):
        """Retourne la classe CSS pour l'affichage du statut."""
        status_classes = {
            'available': 'bg-green-100 text-green-800',
            'low_stock': 'bg-yellow-100 text-yellow-800',
            'out_of_stock': 'bg-red-100 text-red-800',
            'discontinued': 'bg-gray-100 text-gray-800',
            'preorder': 'bg-blue-100 text-blue-800',
        }
        return status_classes.get(self.stock_status, 'bg-gray-100 text-gray-800')


class Quote(models.Model):
    """Devis commercial."""

    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('accepted', 'Accepté'),
        ('rejected', 'Refusé'),
        ('expired', 'Expiré'),
        ('invoiced', 'Facturé'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='quotes'
    )
    number = models.CharField('Numéro', max_length=50)
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='quotes',
        verbose_name='Entreprise'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes',
        verbose_name='Contact'
    )
    # Pour les clients particuliers (sans entreprise)
    client_name = models.CharField('Nom du client', max_length=200, blank=True)
    client_email = models.EmailField('Email du client', blank=True)
    client_phone = models.CharField('Téléphone du client', max_length=20, blank=True)
    client_address = models.TextField('Adresse du client', blank=True)
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    subject = models.CharField('Objet', max_length=200)
    introduction = models.TextField('Introduction', blank=True)
    conditions = models.TextField('Conditions', blank=True)
    validity_days = models.PositiveIntegerField('Validité (jours)', default=30)
    issue_date = models.DateField('Date d\'émission', default=timezone.now)
    expiry_date = models.DateField('Date d\'expiration', null=True, blank=True)

    # Totals (calculated)
    total_ht = models.DecimalField(
        'Total HT',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_vat = models.DecimalField(
        'Total TVA',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_ttc = models.DecimalField(
        'Total TTC',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_quotes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Devis'
        verbose_name_plural = 'Devis'
        ordering = ['-issue_date', '-number']
        unique_together = ['organization', 'number']

    def __str__(self):
        return f"Devis {self.number}"

    def get_absolute_url(self):
        return reverse('invoicing:quote_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.expiry_date:
            self.expiry_date = self.issue_date + timezone.timedelta(days=self.validity_days)
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Recalcule les totaux à partir des lignes."""
        total_ht = Decimal('0.00')
        total_vat = Decimal('0.00')

        for item in self.items.all():
            total_ht += item.total_ht
            total_vat += item.total_vat

        self.total_ht = total_ht
        self.total_vat = total_vat
        self.total_ttc = total_ht + total_vat
        self.save(update_fields=['total_ht', 'total_vat', 'total_ttc'])

    @property
    def is_expired(self):
        return self.expiry_date and self.expiry_date < timezone.now().date()

    def can_convert_to_invoice(self):
        return self.status == 'accepted'


class QuoteItem(models.Model):
    """Ligne de devis."""

    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Produit'
    )
    description = models.CharField('Description', max_length=500)
    quantity = models.DecimalField(
        'Quantité',
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit = models.CharField('Unité', max_length=20, default='unité')
    unit_price = models.DecimalField(
        'Prix unitaire HT',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    vat_rate = models.DecimalField(
        'Taux TVA (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00')
    )
    discount_percent = models.DecimalField(
        'Remise (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    position = models.PositiveIntegerField('Position', default=0)

    class Meta:
        verbose_name = 'Ligne de devis'
        verbose_name_plural = 'Lignes de devis'
        ordering = ['position']

    def __str__(self):
        return self.description

    @property
    def total_ht(self):
        """Total HT après remise."""
        subtotal = self.quantity * self.unit_price
        discount = subtotal * (self.discount_percent / Decimal('100'))
        return subtotal - discount

    @property
    def total_vat(self):
        """Montant TVA."""
        return self.total_ht * (self.vat_rate / Decimal('100'))

    @property
    def total_ttc(self):
        """Total TTC."""
        return self.total_ht + self.total_vat


class Invoice(models.Model):
    """Facture."""

    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('paid', 'Payée'),
        ('partial', 'Partiellement payée'),
        ('overdue', 'En retard'),
        ('cancelled', 'Annulée'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    number = models.CharField('Numéro', max_length=50)

    # Soft delete
    is_deleted = models.BooleanField('Supprimée', default=False)
    deleted_at = models.DateTimeField('Supprimée le', null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='deleted_invoices',
        verbose_name='Supprimée par'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='Entreprise'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='Contact'
    )
    # Pour les clients particuliers (sans entreprise)
    client_name = models.CharField('Nom du client', max_length=200, blank=True)
    client_email = models.EmailField('Email du client', blank=True)
    client_phone = models.CharField('Téléphone du client', max_length=20, blank=True)
    client_address = models.TextField('Adresse du client', blank=True)
    quote = models.ForeignKey(
        Quote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='Devis associé'
    )
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    subject = models.CharField('Objet', max_length=200)
    introduction = models.TextField('Introduction', blank=True)
    conditions = models.TextField(
        'Conditions de paiement',
        blank=True,
        default='Paiement à 30 jours.'
    )
    legal_mentions = models.TextField(
        'Mentions légales',
        blank=True,
        default='En cas de retard de paiement, une pénalité de 3 fois le taux d\'intérêt légal sera appliquée, ainsi qu\'une indemnité forfaitaire de 40€ pour frais de recouvrement.'
    )

    issue_date = models.DateField('Date d\'émission', default=timezone.now)
    due_date = models.DateField('Date d\'échéance')
    payment_terms_days = models.PositiveIntegerField('Délai de paiement (jours)', default=30)

    # Totals
    total_ht = models.DecimalField(
        'Total HT',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_vat = models.DecimalField(
        'Total TVA',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_ttc = models.DecimalField(
        'Total TTC',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    amount_paid = models.DecimalField(
        'Montant payé',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Reminders tracking
    reminder_sent_at = models.DateTimeField('Dernière relance', null=True, blank=True)
    reminder_count = models.PositiveIntegerField('Nombre de relances', default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-issue_date', '-number']
        unique_together = ['organization', 'number']

    def __str__(self):
        return f"Facture {self.number}"

    def get_absolute_url(self):
        return reverse('invoicing:invoice_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.issue_date + timezone.timedelta(days=self.payment_terms_days)
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Recalcule les totaux à partir des lignes."""
        total_ht = Decimal('0.00')
        total_vat = Decimal('0.00')

        for item in self.items.all():
            total_ht += item.total_ht
            total_vat += item.total_vat

        self.total_ht = total_ht
        self.total_vat = total_vat
        self.total_ttc = total_ht + total_vat
        self.save(update_fields=['total_ht', 'total_vat', 'total_ttc'])

    @property
    def balance_due(self):
        """Reste à payer."""
        return self.total_ttc - self.amount_paid

    @property
    def is_overdue(self):
        """Facture en retard de paiement."""
        return (
            self.status not in ('paid', 'cancelled', 'draft') and
            self.due_date < timezone.now().date()
        )

    @property
    def days_overdue(self):
        """Nombre de jours de retard."""
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days

    def update_payment_status(self):
        """Met à jour le statut en fonction des paiements."""
        if self.amount_paid >= self.total_ttc:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        elif self.is_overdue:
            self.status = 'overdue'
        self.save(update_fields=['status'])

    def soft_delete(self, user=None):
        """Effectue une suppression logique de la facture."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restaure une facture supprimée."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class InvoiceItem(models.Model):
    """Ligne de facture."""

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Produit'
    )
    description = models.CharField('Description', max_length=500)
    quantity = models.DecimalField(
        'Quantité',
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit = models.CharField('Unité', max_length=20, default='unité')
    unit_price = models.DecimalField(
        'Prix unitaire HT',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    vat_rate = models.DecimalField(
        'Taux TVA (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00')
    )
    discount_percent = models.DecimalField(
        'Remise (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    position = models.PositiveIntegerField('Position', default=0)

    class Meta:
        verbose_name = 'Ligne de facture'
        verbose_name_plural = 'Lignes de facture'
        ordering = ['position']

    def __str__(self):
        return self.description

    @property
    def total_ht(self):
        """Total HT après remise."""
        subtotal = self.quantity * self.unit_price
        discount = subtotal * (self.discount_percent / Decimal('100'))
        return subtotal - discount

    @property
    def total_vat(self):
        """Montant TVA."""
        return self.total_ht * (self.vat_rate / Decimal('100'))

    @property
    def total_ttc(self):
        """Total TTC."""
        return self.total_ht + self.total_vat


class Payment(models.Model):
    """Paiement reçu pour une facture."""

    METHOD_CHOICES = [
        ('bank_transfer', 'Virement bancaire'),
        ('check', 'Chèque'),
        ('cash', 'Espèces'),
        ('card', 'Carte bancaire'),
        ('other', 'Autre'),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,  # Empêche la suppression si des paiements existent
        related_name='payments'
    )
    amount = models.DecimalField(
        'Montant',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_date = models.DateField('Date de paiement', default=timezone.now)
    method = models.CharField(
        'Mode de paiement',
        max_length=20,
        choices=METHOD_CHOICES,
        default='bank_transfer'
    )
    reference = models.CharField('Référence', max_length=100, blank=True)
    notes = models.TextField('Notes', blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_payments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-payment_date']

    def __str__(self):
        return f"Paiement {self.amount}€ - {self.invoice.number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice payment status
        self.invoice.amount_paid = sum(
            p.amount for p in self.invoice.payments.all()
        )
        self.invoice.update_payment_status()
