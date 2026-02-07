"""
Service de génération de PDF pour les devis et factures.
Utilise WeasyPrint pour la génération de PDFs professionnels.
Supporte plusieurs templates : Classique, Moderne, Minimaliste, Élégant.
"""
import io
from django.template.loader import render_to_string
from django.conf import settings

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


class PDFGenerationError(Exception):
    """Erreur lors de la génération du PDF."""
    pass


class PDFTemplates:
    """Collection de templates CSS pour les documents."""

    # =========================================================================
    # BASE CSS (commun à tous les templates)
    # =========================================================================
    BASE_CSS = """
        @page {
            size: A4;
            margin: 1.5cm 1.5cm 2cm 1.5cm;
            @bottom-center {
                content: "Page " counter(page) " / " counter(pages);
                font-size: 9pt;
                color: #666;
            }
        }

        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.4;
            color: #333;
        }

        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
        }

        .items-table td {
            padding: 12px 10px;
            font-size: 9pt;
        }

        .items-table td.text-center { text-align: center; }
        .items-table td.text-right { text-align: right; }

        .item-description {
            font-weight: 500;
        }

        .totals-section {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 30px;
        }

        .totals-table {
            width: 280px;
            border-collapse: collapse;
        }

        .totals-table td {
            padding: 10px;
            font-size: 10pt;
        }

        .totals-table td:first-child { color: #666; }
        .totals-table td:last-child { text-align: right; font-weight: 500; }

        .legal-mentions {
            font-size: 8pt;
            color: #9ca3af;
            line-height: 1.5;
            border-top: 1px solid #e5e7eb;
            padding-top: 15px;
            margin-top: 20px;
        }
    """

    # =========================================================================
    # TEMPLATE CLASSIQUE - Style professionnel traditionnel
    # =========================================================================
    CLASSIC = BASE_CSS + """
        .document-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid {primary_color};
        }

        .company-info { max-width: 45%; }

        .company-name {
            font-size: 18pt;
            font-weight: bold;
            color: {primary_color};
            margin-bottom: 10px;
        }

        .company-details {
            font-size: 9pt;
            color: #666;
            line-height: 1.6;
        }

        .document-info { text-align: right; }

        .document-type {
            font-size: 24pt;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 10px;
        }

        .document-number {
            font-size: 12pt;
            color: {primary_color};
            font-weight: 600;
        }

        .document-date {
            font-size: 10pt;
            color: #666;
            margin-top: 5px;
        }

        .client-section {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 11pt;
            font-weight: 600;
            color: #374151;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .client-name {
            font-size: 14pt;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 5px;
        }

        .client-details {
            font-size: 9pt;
            color: #666;
            line-height: 1.6;
        }

        .subject-section { margin-bottom: 25px; }
        .subject-label {
            font-size: 9pt;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .subject-text {
            font-size: 12pt;
            font-weight: 600;
            color: #1f2937;
        }

        .introduction {
            margin-bottom: 25px;
            font-size: 10pt;
            color: #4b5563;
            line-height: 1.6;
        }

        .items-table th {
            background: {primary_color};
            color: white;
            padding: 12px 10px;
            text-align: left;
            font-size: 9pt;
            font-weight: 600;
            text-transform: uppercase;
        }

        .items-table th:first-child { border-radius: 6px 0 0 0; }
        .items-table th:last-child { border-radius: 0 6px 0 0; text-align: right; }
        .items-table th.text-center { text-align: center; }
        .items-table th.text-right { text-align: right; }

        .items-table td { border-bottom: 1px solid #e5e7eb; }
        .items-table tr:last-child td { border-bottom: none; }
        .items-table tr:nth-child(even) { background: #f9fafb; }

        .item-description { color: #1f2937; }

        .totals-table tr { border-bottom: 1px solid #e5e7eb; }

        .totals-table tr.total-ttc {
            background: {primary_color};
            border-radius: 6px;
        }

        .totals-table tr.total-ttc td {
            color: white;
            font-weight: bold;
            font-size: 12pt;
            padding: 12px;
        }

        .conditions-section {
            background: #f9fafb;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }

        .conditions-title {
            font-size: 10pt;
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
        }

        .conditions-text {
            font-size: 9pt;
            color: #666;
            line-height: 1.5;
        }

        .validity-section {
            background: #fef3c7;
            padding: 12px 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 9pt;
            color: #92400e;
        }

        .payment-info {
            background: #ecfdf5;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }

        .payment-info-title {
            font-size: 10pt;
            font-weight: 600;
            color: #065f46;
            margin-bottom: 8px;
        }

        .payment-info-details {
            font-size: 9pt;
            color: #047857;
            line-height: 1.6;
        }
    """

    # =========================================================================
    # TEMPLATE MODERNE - Design épuré avec couleurs vives
    # =========================================================================
    MODERN = BASE_CSS + """
        .document-header {
            background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);
            color: white;
            padding: 30px;
            margin: -1.5cm -1.5cm 30px -1.5cm;
        }

        .company-info { max-width: 60%; }

        .company-name {
            font-size: 22pt;
            font-weight: 300;
            margin-bottom: 10px;
        }

        .company-details {
            font-size: 9pt;
            opacity: 0.9;
            line-height: 1.6;
        }

        .document-info {
            text-align: right;
            padding-top: 10px;
        }

        .document-type {
            font-size: 14pt;
            font-weight: 300;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 10px;
        }

        .document-number {
            font-size: 28pt;
            font-weight: 700;
        }

        .document-date {
            font-size: 10pt;
            opacity: 0.9;
            margin-top: 5px;
        }

        .client-section {
            border-left: 4px solid {primary_color};
            padding: 20px;
            margin-bottom: 30px;
            background: #fafafa;
        }

        .section-title {
            font-size: 8pt;
            font-weight: 700;
            color: {primary_color};
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .client-name {
            font-size: 16pt;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 5px;
        }

        .client-details {
            font-size: 9pt;
            color: #666;
            line-height: 1.6;
        }

        .subject-section { margin-bottom: 25px; }
        .subject-label {
            font-size: 8pt;
            color: {primary_color};
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .subject-text {
            font-size: 14pt;
            font-weight: 300;
            color: #1a1a1a;
        }

        .introduction {
            margin-bottom: 25px;
            font-size: 10pt;
            color: #555;
            line-height: 1.8;
        }

        .items-table th {
            background: #1a1a1a;
            color: white;
            padding: 15px 12px;
            text-align: left;
            font-size: 8pt;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .items-table th:last-child { text-align: right; }
        .items-table th.text-center { text-align: center; }
        .items-table th.text-right { text-align: right; }

        .items-table td {
            border-bottom: 1px solid #eee;
            padding: 15px 12px;
        }
        .items-table tr:last-child td { border-bottom: none; }

        .item-description { color: #1a1a1a; }

        .totals-table tr { border-bottom: 1px solid #eee; }

        .totals-table tr.total-ttc {
            background: #1a1a1a;
        }

        .totals-table tr.total-ttc td {
            color: white;
            font-weight: bold;
            font-size: 12pt;
            padding: 15px;
        }

        .conditions-section {
            border: 1px solid #eee;
            padding: 20px;
            margin-bottom: 20px;
        }

        .conditions-title {
            font-size: 8pt;
            font-weight: 700;
            color: {primary_color};
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .conditions-text {
            font-size: 9pt;
            color: #666;
            line-height: 1.6;
        }

        .validity-section {
            background: {primary_color};
            color: white;
            padding: 15px 20px;
            margin-bottom: 20px;
            font-size: 9pt;
        }

        .payment-info {
            border: 2px solid {primary_color};
            padding: 20px;
            margin-bottom: 20px;
        }

        .payment-info-title {
            font-size: 8pt;
            font-weight: 700;
            color: {primary_color};
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .payment-info-details {
            font-size: 9pt;
            color: #333;
            line-height: 1.6;
        }
    """

    # =========================================================================
    # TEMPLATE MINIMALISTE - Très sobre, noir et blanc
    # =========================================================================
    MINIMAL = BASE_CSS + """
        .document-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 1px solid #000;
        }

        .company-info { max-width: 50%; }

        .company-name {
            font-size: 14pt;
            font-weight: 400;
            color: #000;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .company-details {
            font-size: 8pt;
            color: #333;
            line-height: 1.8;
        }

        .document-info { text-align: right; }

        .document-type {
            font-size: 12pt;
            font-weight: 400;
            color: #000;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 15px;
        }

        .document-number {
            font-size: 11pt;
            color: #000;
            font-weight: 400;
        }

        .document-date {
            font-size: 9pt;
            color: #666;
            margin-top: 5px;
        }

        .client-section {
            margin-bottom: 40px;
            padding: 20px 0;
            border-top: 1px solid #eee;
            border-bottom: 1px solid #eee;
        }

        .section-title {
            font-size: 8pt;
            font-weight: 400;
            color: #999;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .client-name {
            font-size: 12pt;
            font-weight: 400;
            color: #000;
            margin-bottom: 5px;
        }

        .client-details {
            font-size: 9pt;
            color: #666;
            line-height: 1.6;
        }

        .subject-section { margin-bottom: 30px; }
        .subject-label {
            font-size: 8pt;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .subject-text {
            font-size: 11pt;
            font-weight: 400;
            color: #000;
        }

        .introduction {
            margin-bottom: 30px;
            font-size: 9pt;
            color: #666;
            line-height: 1.8;
        }

        .items-table th {
            background: #fff;
            color: #000;
            padding: 12px 10px;
            text-align: left;
            font-size: 8pt;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid #000;
        }

        .items-table th:last-child { text-align: right; }
        .items-table th.text-center { text-align: center; }
        .items-table th.text-right { text-align: right; }

        .items-table td {
            border-bottom: 1px solid #eee;
            color: #333;
        }
        .items-table tr:last-child td { border-bottom: 1px solid #000; }

        .item-description {
            color: #000;
            font-weight: 400;
        }

        .totals-table tr { border-bottom: 1px solid #eee; }

        .totals-table td:first-child {
            color: #999;
            font-weight: 400;
        }

        .totals-table tr.total-ttc {
            border-top: 2px solid #000;
            border-bottom: none;
        }

        .totals-table tr.total-ttc td {
            color: #000;
            font-weight: 400;
            font-size: 11pt;
            padding: 15px 10px;
        }

        .conditions-section {
            padding: 20px 0;
            border-top: 1px solid #eee;
            margin-bottom: 20px;
        }

        .conditions-title {
            font-size: 8pt;
            font-weight: 400;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .conditions-text {
            font-size: 8pt;
            color: #666;
            line-height: 1.6;
        }

        .validity-section {
            padding: 15px 0;
            border: 1px solid #000;
            text-align: center;
            margin-bottom: 20px;
            font-size: 9pt;
            color: #000;
        }

        .payment-info {
            padding: 20px 0;
            border-top: 1px solid #eee;
            margin-bottom: 20px;
        }

        .payment-info-title {
            font-size: 8pt;
            font-weight: 400;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .payment-info-details {
            font-size: 9pt;
            color: #333;
            line-height: 1.6;
        }
    """

    # =========================================================================
    # TEMPLATE ÉLÉGANT - Style raffiné avec accents dorés
    # =========================================================================
    ELEGANT = BASE_CSS + """
        @page {
            @bottom-center {
                content: "— " counter(page) " —";
                font-size: 9pt;
                color: #999;
            }
        }

        body {
            font-family: Georgia, 'Times New Roman', serif;
        }

        .document-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            padding-bottom: 25px;
            border-bottom: 3px double {primary_color};
        }

        .company-info { max-width: 50%; }

        .company-name {
            font-size: 20pt;
            font-weight: 400;
            color: {primary_color};
            margin-bottom: 15px;
            font-style: italic;
        }

        .company-details {
            font-size: 9pt;
            color: #555;
            line-height: 1.8;
        }

        .document-info { text-align: right; }

        .document-type {
            font-size: 16pt;
            font-weight: 400;
            color: #333;
            margin-bottom: 10px;
            font-style: italic;
        }

        .document-number {
            font-size: 14pt;
            color: {primary_color};
            font-weight: 600;
        }

        .document-date {
            font-size: 10pt;
            color: #666;
            margin-top: 8px;
            font-style: italic;
        }

        .client-section {
            margin-bottom: 35px;
            padding: 25px;
            border: 1px solid #ddd;
            background: linear-gradient(135deg, #fafafa 0%, #fff 100%);
        }

        .section-title {
            font-size: 9pt;
            font-weight: 600;
            color: {primary_color};
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .client-name {
            font-size: 14pt;
            font-weight: 400;
            color: #222;
            margin-bottom: 8px;
        }

        .client-details {
            font-size: 9pt;
            color: #555;
            line-height: 1.7;
        }

        .subject-section { margin-bottom: 25px; }
        .subject-label {
            font-size: 9pt;
            color: {primary_color};
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .subject-text {
            font-size: 13pt;
            font-weight: 400;
            color: #222;
            font-style: italic;
        }

        .introduction {
            margin-bottom: 30px;
            font-size: 10pt;
            color: #444;
            line-height: 1.8;
            font-style: italic;
        }

        .items-table th {
            background: {primary_color};
            color: white;
            padding: 14px 12px;
            text-align: left;
            font-size: 9pt;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .items-table th:last-child { text-align: right; }
        .items-table th.text-center { text-align: center; }
        .items-table th.text-right { text-align: right; }

        .items-table td {
            border-bottom: 1px solid #e8e8e8;
            padding: 14px 12px;
        }
        .items-table tr:last-child td { border-bottom: none; }
        .items-table tr:nth-child(even) { background: #fcfcfc; }

        .item-description { color: #222; }

        .totals-table tr { border-bottom: 1px solid #e8e8e8; }

        .totals-table tr.total-ttc {
            background: {primary_color};
        }

        .totals-table tr.total-ttc td {
            color: white;
            font-weight: 600;
            font-size: 12pt;
            padding: 14px;
        }

        .conditions-section {
            background: #fafafa;
            padding: 20px;
            border: 1px solid #e8e8e8;
            margin-bottom: 20px;
        }

        .conditions-title {
            font-size: 10pt;
            font-weight: 600;
            color: {primary_color};
            margin-bottom: 10px;
        }

        .conditions-text {
            font-size: 9pt;
            color: #555;
            line-height: 1.6;
            font-style: italic;
        }

        .validity-section {
            background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);
            color: white;
            padding: 15px 20px;
            margin-bottom: 20px;
            font-size: 10pt;
            text-align: center;
            font-style: italic;
        }

        .payment-info {
            border: 2px solid {primary_color};
            padding: 20px;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #fff 0%, #fafafa 100%);
        }

        .payment-info-title {
            font-size: 10pt;
            font-weight: 600;
            color: {primary_color};
            margin-bottom: 10px;
        }

        .payment-info-details {
            font-size: 9pt;
            color: #444;
            line-height: 1.7;
        }
    """

    @classmethod
    def get_template(cls, template_name: str, primary_color: str = "#3B82F6", secondary_color: str = "#1E40AF") -> str:
        """
        Récupère le CSS du template avec les couleurs personnalisées.

        Args:
            template_name: Nom du template (classic, modern, minimal, elegant)
            primary_color: Couleur principale de l'organisation
            secondary_color: Couleur secondaire de l'organisation

        Returns:
            CSS du template avec les couleurs appliquées
        """
        templates = {
            "classic": cls.CLASSIC,
            "modern": cls.MODERN,
            "minimal": cls.MINIMAL,
            "elegant": cls.ELEGANT,
        }

        template_css = templates.get(template_name, cls.CLASSIC)

        # Remplacer les variables de couleur (utiliser replace au lieu de format
        # car le CSS contient des accolades qui seraient interprétées comme placeholders)
        template_css = template_css.replace("{primary_color}", primary_color)
        template_css = template_css.replace("{secondary_color}", secondary_color)
        return template_css


class PDFService:
    """Service de génération de PDF."""

    @classmethod
    def generate_quote_pdf(cls, quote):
        """
        Génère le PDF d'un devis.
        Returns: bytes du PDF
        """
        if not WEASYPRINT_AVAILABLE:
            raise PDFGenerationError(
                "WeasyPrint n'est pas installé. Installez-le avec: pip install weasyprint"
            )

        organization = quote.organization

        # Récupérer le template et les couleurs de l'organisation
        template_name = getattr(organization, 'document_template', 'classic')
        primary_color = getattr(organization, 'primary_color', '#3B82F6')
        secondary_color = getattr(organization, 'secondary_color', '#1E40AF')

        # Render HTML template
        html_content = render_to_string('invoicing/pdf/quote_pdf.html', {
            'quote': quote,
            'organization': organization,
        })

        # Get CSS for the selected template
        template_css = PDFTemplates.get_template(template_name, primary_color, secondary_color)

        # Generate PDF
        try:
            html = HTML(string=html_content, base_url=settings.BASE_DIR)
            css = CSS(string=template_css)
            pdf_bytes = html.write_pdf(stylesheets=[css])
            return pdf_bytes
        except Exception as e:
            raise PDFGenerationError(f"Erreur lors de la génération du PDF: {str(e)}")

    @classmethod
    def generate_invoice_pdf(cls, invoice):
        """
        Génère le PDF d'une facture.
        Returns: bytes du PDF
        """
        if not WEASYPRINT_AVAILABLE:
            raise PDFGenerationError(
                "WeasyPrint n'est pas installé. Installez-le avec: pip install weasyprint"
            )

        organization = invoice.organization

        # Récupérer le template et les couleurs de l'organisation
        template_name = getattr(organization, 'document_template', 'classic')
        primary_color = getattr(organization, 'primary_color', '#3B82F6')
        secondary_color = getattr(organization, 'secondary_color', '#1E40AF')

        # Render HTML template
        html_content = render_to_string('invoicing/pdf/invoice_pdf.html', {
            'invoice': invoice,
            'organization': organization,
        })

        # Get CSS for the selected template
        template_css = PDFTemplates.get_template(template_name, primary_color, secondary_color)

        # Generate PDF
        try:
            html = HTML(string=html_content, base_url=settings.BASE_DIR)
            css = CSS(string=template_css)
            pdf_bytes = html.write_pdf(stylesheets=[css])
            return pdf_bytes
        except Exception as e:
            raise PDFGenerationError(f"Erreur lors de la génération du PDF: {str(e)}")

    @classmethod
    def get_quote_filename(cls, quote):
        """Génère le nom de fichier pour un devis."""
        # Utiliser le nom de l'entreprise ou du client particulier
        if quote.company:
            client_name = quote.company.name
        elif quote.client_name:
            client_name = quote.client_name
        else:
            client_name = "Client"
        safe_client = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_client = safe_client.replace(' ', '_')[:30]
        return f"Devis_{quote.number}_{safe_client}.pdf"

    @classmethod
    def get_invoice_filename(cls, invoice):
        """Génère le nom de fichier pour une facture."""
        # Utiliser le nom de l'entreprise ou du client particulier
        if invoice.company:
            client_name = invoice.company.name
        elif invoice.client_name:
            client_name = invoice.client_name
        else:
            client_name = "Client"
        safe_client = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_client = safe_client.replace(' ', '_')[:30]
        return f"Facture_{invoice.number}_{safe_client}.pdf"

    @classmethod
    def get_available_templates(cls):
        """Retourne la liste des templates disponibles avec aperçu."""
        return [
            {
                "id": "classic",
                "name": "Classique",
                "description": "Style professionnel traditionnel avec en-tête coloré",
            },
            {
                "id": "modern",
                "name": "Moderne",
                "description": "Design épuré avec dégradé et typographie légère",
            },
            {
                "id": "minimal",
                "name": "Minimaliste",
                "description": "Très sobre, noir et blanc, élégant et discret",
            },
            {
                "id": "elegant",
                "name": "Élégant",
                "description": "Style raffiné avec police serif et accents dorés",
            },
        ]
