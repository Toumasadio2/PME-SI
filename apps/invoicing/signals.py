"""
Signals for the invoicing app.
"""
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from .models import Invoice, Payment


@receiver(pre_delete, sender=Invoice)
def invoice_pre_delete(sender, instance, **kwargs):
    """
    Libère le devis associé avant suppression de la facture.
    Remet le statut du devis à 'accepted' pour permettre une nouvelle conversion.
    """
    if instance.quote and instance.quote.status == 'invoiced':
        instance.quote.status = 'accepted'
        instance.quote.save(update_fields=['status'])


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    """
    Met à jour le montant payé et le statut de la facture après un paiement.
    """
    if created:
        invoice = instance.invoice
        invoice.amount_paid = sum(p.amount for p in invoice.payments.all())
        invoice.update_payment_status()
