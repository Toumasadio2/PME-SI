"""
HR Models - Employees, Departments, Leaves, Timesheets, Documents.
"""
import uuid
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TenantModel, TimeStampedModel


class Department(TenantModel):
    """Department/Service within the organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nom", max_length=100)
    code = models.CharField("Code", max_length=20, blank=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
        verbose_name="Responsable"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Département parent"
    )
    description = models.TextField("Description", blank=True)

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ["name"]
        unique_together = ["organization", "code"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("hr:department_detail", kwargs={"pk": self.pk})

    @property
    def employees_count(self) -> int:
        return self.employees.filter(status=Employee.Status.ACTIVE).count()

    def get_hierarchy(self) -> list:
        """Return list of parent departments up to root."""
        hierarchy = []
        current = self.parent
        while current:
            hierarchy.insert(0, current)
            current = current.parent
        return hierarchy


class Position(TenantModel):
    """Job position/title."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField("Intitulé du poste", max_length=150)
    description = models.TextField("Description", blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="positions",
        verbose_name="Département"
    )
    salary_min = models.DecimalField(
        "Salaire minimum",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    salary_max = models.DecimalField(
        "Salaire maximum",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ["department__name", "title"]

    def __str__(self) -> str:
        return f"{self.title} - {self.department.name}"

    def get_absolute_url(self) -> str:
        return reverse("hr:position_detail", kwargs={"pk": self.pk})


class Employee(TenantModel):
    """Employee model with personal and professional information."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Actif"
        ON_NOTICE = "ON_NOTICE", "En préavis"
        SUSPENDED = "SUSPENDED", "Suspendu"
        DEPARTED = "DEPARTED", "Parti"

    class ContractType(models.TextChoices):
        CDI = "CDI", "CDI"
        CDD = "CDD", "CDD"
        STAGE = "STAGE", "Stage"
        ALTERNANCE = "ALTERNANCE", "Alternance"
        INTERIM = "INTERIM", "Intérim"
        FREELANCE = "FREELANCE", "Freelance"

    class Gender(models.TextChoices):
        MALE = "M", "Homme"
        FEMALE = "F", "Femme"
        OTHER = "O", "Autre"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User account link (optional - not all employees have system access)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
        verbose_name="Compte utilisateur"
    )

    # Employee ID (unique per organization)
    employee_id = models.CharField(
        "Matricule",
        max_length=50,
        help_text="Identifiant unique de l'employé"
    )

    # Personal information
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom", max_length=100)
    email = models.EmailField("Email professionnel")
    phone = models.CharField("Téléphone fixe", max_length=20, blank=True)
    mobile = models.CharField("Téléphone mobile", max_length=20, blank=True)
    date_of_birth = models.DateField("Date de naissance", null=True, blank=True)
    gender = models.CharField(
        "Genre",
        max_length=1,
        choices=Gender.choices,
        blank=True
    )
    social_security_number = models.CharField(
        "Numéro de sécurité sociale",
        max_length=15,
        blank=True
    )

    # Address
    address = models.TextField("Adresse", blank=True)
    postal_code = models.CharField("Code postal", max_length=10, blank=True)
    city = models.CharField("Ville", max_length=100, blank=True)
    country = models.CharField("Pays", max_length=100, default="France")

    # Professional information
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name="Département"
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name="Poste"
    )
    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
        verbose_name="Manager"
    )

    # Employment dates
    hire_date = models.DateField("Date d'embauche")
    end_date = models.DateField("Date de fin", null=True, blank=True)

    # Contract information
    contract_type = models.CharField(
        "Type de contrat",
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.CDI
    )
    work_hours = models.DecimalField(
        "Heures hebdomadaires",
        max_digits=4,
        decimal_places=1,
        default=Decimal("35.0"),
        help_text="Ex: 35, 39"
    )
    salary = models.DecimalField(
        "Salaire brut annuel",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Status
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    # Photo
    photo = models.ImageField(
        "Photo",
        upload_to="hr/employees/photos/",
        blank=True
    )

    # Notes
    notes = models.TextField("Notes", blank=True)

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ["last_name", "first_name"]
        unique_together = ["organization", "employee_id"]

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        return reverse("hr:employee_detail", kwargs={"pk": self.pk})

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE

    @property
    def years_of_service(self) -> int:
        """Calculate years of service."""
        if not self.hire_date:
            return 0
        end = self.end_date or timezone.now().date()
        return (end - self.hire_date).days // 365

    @property
    def age(self) -> Optional[int]:
        """Calculate age from date of birth."""
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return (
            today.year - self.date_of_birth.year -
            ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

    def get_initials(self) -> str:
        """Return employee initials."""
        return f"{self.first_name[0]}{self.last_name[0]}".upper()


class LeaveType(TenantModel):
    """Types of leave (vacation, sick, etc.)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nom", max_length=100)
    code = models.CharField("Code", max_length=20)
    description = models.TextField("Description", blank=True)
    is_paid = models.BooleanField("Congé payé", default=True)
    requires_approval = models.BooleanField("Nécessite approbation", default=True)
    max_days_per_year = models.PositiveIntegerField(
        "Maximum jours/an",
        null=True,
        blank=True,
        help_text="Laisser vide si illimité"
    )
    accrual_rate = models.DecimalField(
        "Taux d'acquisition",
        max_digits=4,
        decimal_places=2,
        default=Decimal("0"),
        help_text="Jours acquis par mois (ex: 2.5 pour CP)"
    )
    color = models.CharField(
        "Couleur",
        max_length=7,
        default="#3B82F6",
        help_text="Code couleur pour le calendrier"
    )
    is_active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Type de congé"
        verbose_name_plural = "Types de congés"
        ordering = ["name"]
        unique_together = ["organization", "code"]

    def __str__(self) -> str:
        return self.name


class LeaveBalance(TenantModel):
    """Leave balance for an employee for a specific leave type and year."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_balances",
        verbose_name="Employé"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="balances",
        verbose_name="Type de congé"
    )
    year = models.PositiveIntegerField("Année")
    acquired = models.DecimalField(
        "Jours acquis",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0")
    )
    taken = models.DecimalField(
        "Jours pris",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0")
    )
    pending = models.DecimalField(
        "En attente",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
        help_text="Jours en attente de validation"
    )
    carried_over = models.DecimalField(
        "Report N-1",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
        help_text="Jours reportés de l'année précédente"
    )

    class Meta:
        verbose_name = "Solde de congés"
        verbose_name_plural = "Soldes de congés"
        unique_together = ["employee", "leave_type", "year"]

    def __str__(self) -> str:
        return f"{self.employee} - {self.leave_type} ({self.year})"

    @property
    def available(self) -> Decimal:
        """Calculate available days."""
        return self.acquired + self.carried_over - self.taken - self.pending

    @property
    def total_acquired(self) -> Decimal:
        """Total acquired including carried over."""
        return self.acquired + self.carried_over


class LeaveRequest(TenantModel):
    """Leave request made by an employee."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        PENDING = "PENDING", "En attente"
        APPROVED = "APPROVED", "Approuvé"
        REJECTED = "REJECTED", "Refusé"
        CANCELLED = "CANCELLED", "Annulé"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_requests",
        verbose_name="Employé"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="requests",
        verbose_name="Type de congé"
    )
    start_date = models.DateField("Date de début")
    end_date = models.DateField("Date de fin")
    start_half_day = models.BooleanField(
        "Demi-journée début",
        default=False,
        help_text="Cocher si commence l'après-midi"
    )
    end_half_day = models.BooleanField(
        "Demi-journée fin",
        default=False,
        help_text="Cocher si finit le matin"
    )
    days_count = models.DecimalField(
        "Nombre de jours",
        max_digits=5,
        decimal_places=2,
        help_text="Calculé automatiquement"
    )
    reason = models.TextField("Motif", blank=True)
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leave_requests",
        verbose_name="Approuvé par"
    )
    approved_at = models.DateTimeField("Date d'approbation", null=True, blank=True)
    rejection_reason = models.TextField("Motif de refus", blank=True)

    class Meta:
        verbose_name = "Demande de congé"
        verbose_name_plural = "Demandes de congés"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.employee} - {self.leave_type} ({self.start_date} - {self.end_date})"

    def get_absolute_url(self) -> str:
        return reverse("hr:leave_detail", kwargs={"pk": self.pk})

    @property
    def is_pending(self) -> bool:
        return self.status == self.Status.PENDING

    @property
    def can_be_cancelled(self) -> bool:
        """Check if request can still be cancelled."""
        return self.status in [self.Status.DRAFT, self.Status.PENDING]


class Timesheet(TenantModel):
    """Daily timesheet entry."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        SUBMITTED = "SUBMITTED", "Soumis"
        VALIDATED = "VALIDATED", "Validé"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="timesheets",
        verbose_name="Employé"
    )
    date = models.DateField("Date")
    start_time = models.TimeField("Heure de début", null=True, blank=True)
    end_time = models.TimeField("Heure de fin", null=True, blank=True)
    break_duration = models.DurationField(
        "Durée pause",
        null=True,
        blank=True,
        help_text="Format: HH:MM:SS"
    )
    worked_hours = models.DecimalField(
        "Heures travaillées",
        max_digits=4,
        decimal_places=2,
        default=Decimal("0")
    )
    overtime_hours = models.DecimalField(
        "Heures supplémentaires",
        max_digits=4,
        decimal_places=2,
        default=Decimal("0")
    )
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    notes = models.TextField("Notes", blank=True)

    class Meta:
        verbose_name = "Feuille de temps"
        verbose_name_plural = "Feuilles de temps"
        ordering = ["-date"]
        unique_together = ["employee", "date"]

    def __str__(self) -> str:
        return f"{self.employee} - {self.date}"

    def calculate_hours(self) -> None:
        """Calculate worked hours from start/end times."""
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta

            start_dt = datetime.combine(self.date, self.start_time)
            end_dt = datetime.combine(self.date, self.end_time)

            # Handle overnight shifts
            if end_dt < start_dt:
                end_dt += timedelta(days=1)

            duration = end_dt - start_dt

            # Subtract break
            if self.break_duration:
                duration -= self.break_duration

            self.worked_hours = Decimal(duration.total_seconds() / 3600).quantize(
                Decimal("0.01")
            )


class Attendance(TimeStampedModel):
    """Clock in/out records."""

    class Source(models.TextChoices):
        MANUAL = "MANUAL", "Manuel"
        BADGE = "BADGE", "Badge"
        APP = "APP", "Application"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="Employé"
    )
    date = models.DateField("Date")
    clock_in = models.DateTimeField("Pointage entrée")
    clock_out = models.DateTimeField("Pointage sortie", null=True, blank=True)
    source = models.CharField(
        "Source",
        max_length=10,
        choices=Source.choices,
        default=Source.MANUAL
    )
    notes = models.TextField("Notes", blank=True)

    class Meta:
        verbose_name = "Pointage"
        verbose_name_plural = "Pointages"
        ordering = ["-date", "-clock_in"]

    def __str__(self) -> str:
        return f"{self.employee} - {self.date}"

    @property
    def duration(self):
        """Calculate duration between clock in and out."""
        if self.clock_in and self.clock_out:
            return self.clock_out - self.clock_in
        return None


class HRDocument(TenantModel):
    """HR documents attached to employees."""

    class DocumentType(models.TextChoices):
        CONTRACT = "CONTRACT", "Contrat"
        AMENDMENT = "AMENDMENT", "Avenant"
        ATTESTATION = "ATTESTATION", "Attestation"
        CERTIFICATE = "CERTIFICATE", "Certificat"
        PAYSLIP = "PAYSLIP", "Bulletin de paie"
        ID_DOCUMENT = "ID_DOCUMENT", "Pièce d'identité"
        DIPLOMA = "DIPLOMA", "Diplôme"
        OTHER = "OTHER", "Autre"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Employé"
    )
    document_type = models.CharField(
        "Type de document",
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )
    title = models.CharField("Titre", max_length=255)
    file = models.FileField(
        "Fichier",
        upload_to="hr/documents/%Y/%m/"
    )
    file_size = models.PositiveIntegerField("Taille (octets)", default=0)
    is_confidential = models.BooleanField("Confidentiel", default=False)
    valid_from = models.DateField("Valide à partir de", null=True, blank=True)
    valid_until = models.DateField("Valide jusqu'à", null=True, blank=True)
    notes = models.TextField("Notes", blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_hr_documents"
    )

    class Meta:
        verbose_name = "Document RH"
        verbose_name_plural = "Documents RH"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} - {self.employee}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    @property
    def file_extension(self) -> str:
        return self.file.name.split(".")[-1].lower() if self.file else ""

    @property
    def is_expired(self) -> bool:
        if self.valid_until:
            return self.valid_until < timezone.now().date()
        return False


class EmployeeHistory(TimeStampedModel):
    """History of employee career events."""

    class EventType(models.TextChoices):
        HIRE = "HIRE", "Embauche"
        PROMOTION = "PROMOTION", "Promotion"
        SALARY_CHANGE = "SALARY_CHANGE", "Changement de salaire"
        DEPARTMENT_CHANGE = "DEPARTMENT_CHANGE", "Changement de département"
        POSITION_CHANGE = "POSITION_CHANGE", "Changement de poste"
        CONTRACT_CHANGE = "CONTRACT_CHANGE", "Changement de contrat"
        TRAINING = "TRAINING", "Formation"
        DEPARTURE = "DEPARTURE", "Départ"
        WARNING = "WARNING", "Avertissement"
        NOTE = "NOTE", "Note"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="Employé"
    )
    event_type = models.CharField(
        "Type d'événement",
        max_length=20,
        choices=EventType.choices
    )
    event_date = models.DateField("Date de l'événement")
    description = models.TextField("Description")
    old_value = models.JSONField("Ancienne valeur", default=dict, blank=True)
    new_value = models.JSONField("Nouvelle valeur", default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_employee_history"
    )

    class Meta:
        verbose_name = "Historique employé"
        verbose_name_plural = "Historiques employés"
        ordering = ["-event_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.employee} - {self.get_event_type_display()} ({self.event_date})"


class HRDocumentTemplate(TenantModel):
    """Templates for generating HR documents."""

    class TemplateType(models.TextChoices):
        CONTRACT = "CONTRACT", "Contrat"
        ATTESTATION = "ATTESTATION", "Attestation"
        CERTIFICATE = "CERTIFICATE", "Certificat"
        LETTER = "LETTER", "Courrier"
        OTHER = "OTHER", "Autre"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nom", max_length=255)
    document_type = models.CharField(
        "Type de document",
        max_length=20,
        choices=TemplateType.choices,
        default=TemplateType.OTHER
    )
    content = models.TextField(
        "Contenu",
        help_text="HTML avec variables {{ employee.first_name }}, etc."
    )
    variables = models.JSONField(
        "Variables disponibles",
        default=list,
        help_text="Liste des variables utilisables dans le template"
    )
    is_active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Modèle de document"
        verbose_name_plural = "Modèles de documents"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
