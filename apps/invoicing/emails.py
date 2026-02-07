"""
Service d'envoi d'emails pour les devis et factures.
"""
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

from .pdf import PDFService, PDFGenerationError


class EmailService:
    """Service d'envoi d'emails pour les documents de facturation."""

    @classmethod
    def send_quote(cls, quote, recipient_email=None, message=None):
        """
        Envoie un devis par email avec le PDF en pièce jointe.

        Args:
            quote: Instance du devis
            recipient_email: Email du destinataire (si None, utilise l'email de la société)
            message: Message personnalisé (optionnel)

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        # Determine recipient
        if not recipient_email:
            if quote.contact and quote.contact.email:
                recipient_email = quote.contact.email
            elif quote.company.email:
                recipient_email = quote.company.email
            else:
                raise ValueError("Aucune adresse email disponible pour ce client.")

        # Generate PDF
        try:
            pdf_bytes = PDFService.generate_quote_pdf(quote)
            pdf_filename = PDFService.get_quote_filename(quote)
        except PDFGenerationError as e:
            raise ValueError(f"Impossible de générer le PDF: {str(e)}")

        # Prepare email content
        context = {
            'quote': quote,
            'organization': quote.organization,
            'custom_message': message,
        }

        subject = f"Devis {quote.number} - {quote.organization.name}"
        html_content = render_to_string('invoicing/emails/quote_email.html', context)
        text_content = render_to_string('invoicing/emails/quote_email.txt', context)

        # Create and send email
        email = EmailMessage(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.attach(pdf_filename, pdf_bytes, 'application/pdf')

        # Send
        sent = email.send(fail_silently=False)

        if sent:
            # Update quote status if still draft
            if quote.status == 'draft':
                quote.status = 'sent'
                quote.save(update_fields=['status'])

        return bool(sent)

    @classmethod
    def send_invoice(cls, invoice, recipient_email=None, message=None):
        """
        Envoie une facture par email avec le PDF en pièce jointe.

        Args:
            invoice: Instance de la facture
            recipient_email: Email du destinataire (si None, utilise l'email de la société)
            message: Message personnalisé (optionnel)

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        # Determine recipient
        if not recipient_email:
            if invoice.contact and invoice.contact.email:
                recipient_email = invoice.contact.email
            elif invoice.company.email:
                recipient_email = invoice.company.email
            else:
                raise ValueError("Aucune adresse email disponible pour ce client.")

        # Generate PDF
        try:
            pdf_bytes = PDFService.generate_invoice_pdf(invoice)
            pdf_filename = PDFService.get_invoice_filename(invoice)
        except PDFGenerationError as e:
            raise ValueError(f"Impossible de générer le PDF: {str(e)}")

        # Prepare email content
        context = {
            'invoice': invoice,
            'organization': invoice.organization,
            'custom_message': message,
        }

        subject = f"Facture {invoice.number} - {invoice.organization.name}"
        html_content = render_to_string('invoicing/emails/invoice_email.html', context)
        text_content = render_to_string('invoicing/emails/invoice_email.txt', context)

        # Create and send email
        email = EmailMessage(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.attach(pdf_filename, pdf_bytes, 'application/pdf')

        # Send
        sent = email.send(fail_silently=False)

        if sent:
            # Update invoice status if still draft
            if invoice.status == 'draft':
                invoice.status = 'sent'
                invoice.save(update_fields=['status'])

        return bool(sent)

    @classmethod
    def send_reminder(cls, invoice, recipient_email=None, message=None):
        """
        Envoie une relance pour une facture impayée.

        Args:
            invoice: Instance de la facture
            recipient_email: Email du destinataire
            message: Message personnalisé (optionnel)

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        # Determine recipient
        if not recipient_email:
            if invoice.contact and invoice.contact.email:
                recipient_email = invoice.contact.email
            elif invoice.company.email:
                recipient_email = invoice.company.email
            else:
                raise ValueError("Aucune adresse email disponible pour ce client.")

        # Generate PDF
        try:
            pdf_bytes = PDFService.generate_invoice_pdf(invoice)
            pdf_filename = PDFService.get_invoice_filename(invoice)
        except PDFGenerationError as e:
            raise ValueError(f"Impossible de générer le PDF: {str(e)}")

        # Determine reminder level
        reminder_level = invoice.reminder_count + 1
        if reminder_level == 1:
            reminder_text = "Première relance"
        elif reminder_level == 2:
            reminder_text = "Deuxième relance"
        else:
            reminder_text = f"Relance n°{reminder_level}"

        # Prepare email content
        context = {
            'invoice': invoice,
            'organization': invoice.organization,
            'reminder_level': reminder_level,
            'reminder_text': reminder_text,
            'custom_message': message,
        }

        subject = f"[{reminder_text}] Facture {invoice.number} - {invoice.organization.name}"
        html_content = render_to_string('invoicing/emails/reminder_email.html', context)
        text_content = render_to_string('invoicing/emails/reminder_email.txt', context)

        # Create and send email
        email = EmailMessage(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.attach(pdf_filename, pdf_bytes, 'application/pdf')

        # Send
        sent = email.send(fail_silently=False)

        if sent:
            # Update reminder tracking
            invoice.reminder_count = reminder_level
            invoice.reminder_sent_at = timezone.now()
            invoice.save(update_fields=['reminder_count', 'reminder_sent_at'])

        return bool(sent)
