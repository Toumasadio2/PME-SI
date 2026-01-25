"""
CRM Models - Contacts, Companies, Opportunities, Activities.
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TenantModel, TimeStampedModel


class Tag(TenantModel):
    """Tags for categorizing contacts and companies."""

    name = models.CharField(max_length=50)
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Hex color code"
    )

    class Meta:
        ordering = ["name"]
        unique_together = ["organization", "name"]

    def __str__(self) -> str:
        return self.name


class PipelineStage(TenantModel):
    """Customizable pipeline stages for opportunities."""

    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    probability = models.PositiveIntegerField(
        default=0,
        help_text="Default win probability percentage (0-100)"
    )
    color = models.CharField(max_length=7, default="#6B7280")
    is_won = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        unique_together = ["organization", "name"]

    def __str__(self) -> str:
        return self.name


class Company(TenantModel):
    """Company/Enterprise model."""

    class Category(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        PROSPECT = "PROSPECT", "Prospect"
        PARTNER = "PARTNER", "Partenaire"
        SUPPLIER = "SUPPLIER", "Fournisseur"
        OTHER = "OTHER", "Autre"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Raison sociale", max_length=255)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.PROSPECT
    )

    # Legal info
    siret = models.CharField("SIRET", max_length=14, blank=True)
    vat_number = models.CharField("N° TVA", max_length=20, blank=True)

    # Address
    address = models.TextField("Adresse", blank=True)
    postal_code = models.CharField("Code postal", max_length=10, blank=True)
    city = models.CharField("Ville", max_length=100, blank=True)
    country = models.CharField("Pays", max_length=100, default="France")

    # Contact info
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    website = models.URLField("Site web", blank=True)

    # Commercial info
    industry = models.CharField("Secteur d'activité", max_length=100, blank=True)
    employees_count = models.PositiveIntegerField("Nombre d'employés", null=True, blank=True)
    annual_revenue = models.DecimalField(
        "CA annuel",
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Relations
    tags = models.ManyToManyField(Tag, blank=True, related_name="companies")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_companies",
        verbose_name="Commercial assigné"
    )

    # Notes
    notes = models.TextField("Notes", blank=True)

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("crm:company_detail", kwargs={"pk": self.pk})

    @property
    def contacts_count(self) -> int:
        return self.contacts.count()

    @property
    def opportunities_count(self) -> int:
        return self.opportunities.count()

    @property
    def total_opportunities_value(self) -> Decimal:
        return self.opportunities.aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")


class Contact(TenantModel):
    """Contact/Person model."""

    class Category(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        PROSPECT = "PROSPECT", "Prospect"
        PARTNER = "PARTNER", "Partenaire"
        OTHER = "OTHER", "Autre"

    class Civility(models.TextChoices):
        MR = "MR", "M."
        MRS = "MRS", "Mme"
        MS = "MS", "Mlle"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identity
    civility = models.CharField(
        max_length=5,
        choices=Civility.choices,
        blank=True
    )
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom", max_length=100)

    # Professional info
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts",
        verbose_name="Entreprise"
    )
    job_title = models.CharField("Fonction", max_length=100, blank=True)
    department = models.CharField("Service", max_length=100, blank=True)

    # Contact info
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    mobile = models.CharField("Mobile", max_length=20, blank=True)

    # Address (if different from company)
    address = models.TextField("Adresse", blank=True)
    postal_code = models.CharField("Code postal", max_length=10, blank=True)
    city = models.CharField("Ville", max_length=100, blank=True)
    country = models.CharField("Pays", max_length=100, blank=True)

    # Categorization
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.PROSPECT
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="contacts")

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_contacts",
        verbose_name="Commercial assigné"
    )

    # Preferences
    accepts_marketing = models.BooleanField("Accepte les communications marketing", default=False)
    preferred_contact_method = models.CharField(
        "Méthode de contact préférée",
        max_length=20,
        choices=[
            ("email", "Email"),
            ("phone", "Téléphone"),
            ("mobile", "Mobile"),
        ],
        default="email"
    )

    # Notes
    notes = models.TextField("Notes", blank=True)

    # Activity tracking
    last_activity_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        return reverse("crm:contact_detail", kwargs={"pk": self.pk})

    @property
    def full_name(self) -> str:
        parts = []
        if self.civility:
            parts.append(self.get_civility_display())
        parts.append(self.first_name)
        parts.append(self.last_name)
        return " ".join(parts)

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def update_last_activity(self) -> None:
        self.last_activity_date = timezone.now()
        self.save(update_fields=["last_activity_date"])


class Opportunity(TenantModel):
    """Sales opportunity model."""

    class Priority(models.TextChoices):
        LOW = "LOW", "Basse"
        MEDIUM = "MEDIUM", "Moyenne"
        HIGH = "HIGH", "Haute"
        CRITICAL = "CRITICAL", "Critique"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nom de l'opportunité", max_length=255)

    # Relations
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="opportunities",
        verbose_name="Entreprise"
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunities",
        verbose_name="Contact principal"
    )

    # Pipeline
    stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.PROTECT,
        related_name="opportunities",
        verbose_name="Étape"
    )

    # Financial
    amount = models.DecimalField(
        "Montant",
        max_digits=15,
        decimal_places=2,
        default=Decimal("0")
    )
    probability = models.PositiveIntegerField(
        "Probabilité (%)",
        default=0,
        help_text="Probabilité de gain (0-100)"
    )

    # Dates
    expected_close_date = models.DateField(
        "Date de clôture prévue",
        null=True,
        blank=True
    )
    closed_date = models.DateField(
        "Date de clôture réelle",
        null=True,
        blank=True
    )

    # Details
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    source = models.CharField(
        "Source",
        max_length=100,
        blank=True,
        help_text="Comment avez-vous trouvé cette opportunité?"
    )
    description = models.TextField("Description", blank=True)
    next_step = models.CharField("Prochaine étape", max_length=255, blank=True)

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_opportunities",
        verbose_name="Commercial assigné"
    )

    # Tracking
    lost_reason = models.TextField("Raison de perte", blank=True)

    class Meta:
        verbose_name = "Opportunité"
        verbose_name_plural = "Opportunités"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} - {self.company.name}"

    def get_absolute_url(self) -> str:
        return reverse("crm:opportunity_detail", kwargs={"pk": self.pk})

    @property
    def weighted_amount(self) -> Decimal:
        """Amount weighted by probability."""
        return self.amount * Decimal(self.probability) / Decimal(100)

    @property
    def is_won(self) -> bool:
        return self.stage.is_won if self.stage else False

    @property
    def is_lost(self) -> bool:
        return self.stage.is_lost if self.stage else False

    @property
    def is_open(self) -> bool:
        return not self.is_won and not self.is_lost

    def move_to_stage(self, stage: PipelineStage) -> None:
        """Move opportunity to a new stage."""
        self.stage = stage
        self.probability = stage.probability

        if stage.is_won or stage.is_lost:
            self.closed_date = timezone.now().date()
        else:
            self.closed_date = None

        self.save()


class Activity(TenantModel):
    """Activity/Interaction model for tracking contacts with leads."""

    class ActivityType(models.TextChoices):
        CALL = "CALL", "Appel"
        EMAIL = "EMAIL", "Email"
        MEETING = "MEETING", "Réunion"
        NOTE = "NOTE", "Note"
        TASK = "TASK", "Tâche"
        DEMO = "DEMO", "Démonstration"
        PROPOSAL = "PROPOSAL", "Proposition"
        OTHER = "OTHER", "Autre"

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planifié"
        COMPLETED = "COMPLETED", "Terminé"
        CANCELLED = "CANCELLED", "Annulé"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Type and status
    activity_type = models.CharField(
        "Type",
        max_length=20,
        choices=ActivityType.choices,
        default=ActivityType.NOTE
    )
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=Status.choices,
        default=Status.COMPLETED
    )

    # Content
    subject = models.CharField("Sujet", max_length=255)
    description = models.TextField("Description", blank=True)

    # Relations (at least one required)
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name="Contact"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name="Entreprise"
    )
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name="Opportunité"
    )

    # Scheduling
    scheduled_date = models.DateTimeField(
        "Date planifiée",
        null=True,
        blank=True
    )
    completed_date = models.DateTimeField(
        "Date de réalisation",
        null=True,
        blank=True
    )
    duration_minutes = models.PositiveIntegerField(
        "Durée (minutes)",
        null=True,
        blank=True
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_activities",
        verbose_name="Assigné à"
    )

    # Reminder
    reminder_date = models.DateTimeField(
        "Date de rappel",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_activity_type_display()} - {self.subject}"

    def get_absolute_url(self) -> str:
        return reverse("crm:activity_detail", kwargs={"pk": self.pk})

    def complete(self) -> None:
        """Mark activity as completed."""
        self.status = self.Status.COMPLETED
        self.completed_date = timezone.now()
        self.save()

        # Update contact's last activity
        if self.contact:
            self.contact.update_last_activity()

    @property
    def is_overdue(self) -> bool:
        """Check if planned activity is overdue."""
        if self.status == self.Status.PLANNED and self.scheduled_date:
            return self.scheduled_date < timezone.now()
        return False


class Document(TenantModel):
    """Document attached to CRM entities."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nom", max_length=255)
    file = models.FileField("Fichier", upload_to="crm/documents/%Y/%m/")
    description = models.TextField("Description", blank=True)

    # Relations
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents"
    )
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents"
    )

    # Metadata
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_documents"
    )

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    @property
    def file_extension(self) -> str:
        return self.file.name.split(".")[-1].lower() if self.file else ""

    @property
    def file_size(self) -> int:
        try:
            return self.file.size
        except (ValueError, FileNotFoundError):
            return 0
