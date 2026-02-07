"""HR Admin configuration."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Attendance,
    Department,
    Employee,
    EmployeeHistory,
    HRDocument,
    HRDocumentTemplate,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    Position,
    Timesheet,
)


class PositionInline(admin.TabularInline):
    """Inline for positions within a department."""

    model = Position
    extra = 0
    fields = ["title", "salary_min", "salary_max", "is_active"]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Admin configuration for Department."""

    list_display = ["name", "code", "manager", "parent", "employees_count", "organization"]
    list_filter = ["organization"]
    search_fields = ["name", "code"]
    ordering = ["name"]
    autocomplete_fields = ["manager", "parent"]
    inlines = [PositionInline]

    fieldsets = (
        (None, {
            "fields": ("organization", "name", "code", "description")
        }),
        ("Hiérarchie", {
            "fields": ("parent", "manager")
        }),
    )


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Admin configuration for Position."""

    list_display = ["title", "department", "salary_range", "is_active", "organization"]
    list_filter = ["organization", "department", "is_active"]
    search_fields = ["title", "description"]
    ordering = ["department__name", "title"]
    autocomplete_fields = ["department"]

    @admin.display(description="Fourchette salariale")
    def salary_range(self, obj):
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_min:,.0f}€ - {obj.salary_max:,.0f}€"
        elif obj.salary_min:
            return f"À partir de {obj.salary_min:,.0f}€"
        elif obj.salary_max:
            return f"Jusqu'à {obj.salary_max:,.0f}€"
        return "-"


class EmployeeHistoryInline(admin.TabularInline):
    """Inline for employee history."""

    model = EmployeeHistory
    extra = 0
    readonly_fields = ["event_type", "event_date", "description", "created_by", "created_at"]
    ordering = ["-event_date"]


class HRDocumentInline(admin.TabularInline):
    """Inline for employee documents."""

    model = HRDocument
    extra = 0
    fields = ["document_type", "title", "file", "is_confidential", "valid_until"]
    readonly_fields = ["file_size", "uploaded_by"]


class LeaveBalanceInline(admin.TabularInline):
    """Inline for employee leave balances."""

    model = LeaveBalance
    extra = 0
    fields = ["leave_type", "year", "acquired", "taken", "pending", "carried_over"]
    ordering = ["-year", "leave_type__name"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Admin configuration for Employee."""

    list_display = [
        "employee_id", "full_name", "department", "position",
        "contract_type", "status", "hire_date", "organization"
    ]
    list_filter = [
        "organization", "status", "contract_type", "department"
    ]
    search_fields = ["first_name", "last_name", "employee_id", "email"]
    ordering = ["last_name", "first_name"]
    date_hierarchy = "hire_date"
    autocomplete_fields = ["user", "department", "position", "manager"]
    readonly_fields = ["years_of_service", "age"]
    inlines = [LeaveBalanceInline, HRDocumentInline, EmployeeHistoryInline]

    fieldsets = (
        ("Identification", {
            "fields": ("organization", "employee_id", "user", "status")
        }),
        ("Informations personnelles", {
            "fields": (
                ("first_name", "last_name"),
                ("email", "phone", "mobile"),
                ("date_of_birth", "gender"),
                "social_security_number",
                "photo"
            )
        }),
        ("Adresse", {
            "fields": (
                "address",
                ("postal_code", "city"),
                "country"
            ),
            "classes": ["collapse"]
        }),
        ("Informations professionnelles", {
            "fields": (
                ("department", "position"),
                "manager",
                ("hire_date", "end_date")
            )
        }),
        ("Contrat", {
            "fields": (
                "contract_type",
                ("work_hours", "salary")
            )
        }),
        ("Statistiques", {
            "fields": ("years_of_service", "age"),
            "classes": ["collapse"]
        }),
        ("Notes", {
            "fields": ("notes",),
            "classes": ["collapse"]
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "department", "position", "manager", "organization"
        )


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    """Admin configuration for LeaveType."""

    list_display = [
        "name", "code", "is_paid", "requires_approval",
        "max_days_per_year", "accrual_rate", "color_preview", "is_active", "organization"
    ]
    list_filter = ["organization", "is_paid", "requires_approval", "is_active"]
    search_fields = ["name", "code"]
    ordering = ["name"]

    fieldsets = (
        (None, {
            "fields": ("organization", "name", "code", "description")
        }),
        ("Paramètres", {
            "fields": (
                ("is_paid", "requires_approval"),
                ("max_days_per_year", "accrual_rate"),
                "color",
                "is_active"
            )
        }),
    )

    @admin.display(description="Couleur")
    def color_preview(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 10px; border-radius: 3px;">&nbsp;</span>',
            obj.color
        )


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    """Admin configuration for LeaveBalance."""

    list_display = [
        "employee", "leave_type", "year", "acquired",
        "taken", "pending", "available"
    ]
    list_filter = ["year", "leave_type"]
    search_fields = ["employee__first_name", "employee__last_name"]
    ordering = ["-year", "employee__last_name"]
    autocomplete_fields = ["employee", "leave_type"]

    @admin.display(description="Disponible")
    def available(self, obj):
        return obj.available


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    """Admin configuration for LeaveRequest."""

    list_display = [
        "employee", "leave_type", "start_date", "end_date",
        "days_count", "status", "approved_by", "organization"
    ]
    list_filter = ["organization", "status", "leave_type"]
    search_fields = ["employee__first_name", "employee__last_name"]
    ordering = ["-created_at"]
    date_hierarchy = "start_date"
    autocomplete_fields = ["employee", "leave_type", "approved_by"]
    readonly_fields = ["days_count", "approved_at"]
    actions = ["approve_requests", "reject_requests"]

    fieldsets = (
        (None, {
            "fields": ("organization", "employee", "leave_type", "status")
        }),
        ("Période", {
            "fields": (
                ("start_date", "end_date"),
                ("start_half_day", "end_half_day"),
                "days_count"
            )
        }),
        ("Détails", {
            "fields": ("reason",)
        }),
        ("Approbation", {
            "fields": (
                ("approved_by", "approved_at"),
                "rejection_reason"
            )
        }),
    )

    @admin.action(description="Approuver les demandes sélectionnées")
    def approve_requests(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status=LeaveRequest.Status.PENDING).update(
            status=LeaveRequest.Status.APPROVED,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f"{count} demande(s) approuvée(s).")

    @admin.action(description="Refuser les demandes sélectionnées")
    def reject_requests(self, request, queryset):
        count = queryset.filter(status=LeaveRequest.Status.PENDING).update(
            status=LeaveRequest.Status.REJECTED
        )
        self.message_user(request, f"{count} demande(s) refusée(s).")


@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    """Admin configuration for Timesheet."""

    list_display = [
        "employee", "date", "start_time", "end_time",
        "worked_hours", "overtime_hours", "status"
    ]
    list_filter = ["status", "employee__department"]
    search_fields = ["employee__first_name", "employee__last_name"]
    ordering = ["-date"]
    date_hierarchy = "date"
    autocomplete_fields = ["employee"]

    fieldsets = (
        (None, {
            "fields": ("organization", "employee", "date", "status")
        }),
        ("Horaires", {
            "fields": (
                ("start_time", "end_time"),
                "break_duration",
                ("worked_hours", "overtime_hours")
            )
        }),
        ("Notes", {
            "fields": ("notes",),
            "classes": ["collapse"]
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin configuration for Attendance."""

    list_display = ["employee", "date", "clock_in", "clock_out", "source", "duration"]
    list_filter = ["source", "date"]
    search_fields = ["employee__first_name", "employee__last_name"]
    ordering = ["-date", "-clock_in"]
    date_hierarchy = "date"
    autocomplete_fields = ["employee"]

    @admin.display(description="Durée")
    def duration(self, obj):
        if obj.duration:
            hours, remainder = divmod(obj.duration.seconds, 3600)
            minutes = remainder // 60
            return f"{hours}h{minutes:02d}"
        return "-"


@admin.register(HRDocument)
class HRDocumentAdmin(admin.ModelAdmin):
    """Admin configuration for HRDocument."""

    list_display = [
        "title", "employee", "document_type", "is_confidential",
        "valid_until", "is_expired", "organization"
    ]
    list_filter = ["organization", "document_type", "is_confidential"]
    search_fields = ["title", "employee__first_name", "employee__last_name"]
    ordering = ["-created_at"]
    autocomplete_fields = ["employee", "uploaded_by"]
    readonly_fields = ["file_size", "uploaded_by", "created_at"]

    fieldsets = (
        (None, {
            "fields": ("organization", "employee", "document_type", "title")
        }),
        ("Fichier", {
            "fields": ("file", "file_size")
        }),
        ("Validité", {
            "fields": (
                ("valid_from", "valid_until"),
                "is_confidential"
            )
        }),
        ("Métadonnées", {
            "fields": ("notes", "uploaded_by", "created_at"),
            "classes": ["collapse"]
        }),
    )

    @admin.display(description="Expiré", boolean=True)
    def is_expired(self, obj):
        return obj.is_expired


@admin.register(EmployeeHistory)
class EmployeeHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for EmployeeHistory."""

    list_display = [
        "employee", "event_type", "event_date", "description", "created_by"
    ]
    list_filter = ["event_type"]
    search_fields = ["employee__first_name", "employee__last_name", "description"]
    ordering = ["-event_date"]
    date_hierarchy = "event_date"
    autocomplete_fields = ["employee", "created_by"]
    readonly_fields = ["created_at"]

    fieldsets = (
        (None, {
            "fields": ("employee", "event_type", "event_date")
        }),
        ("Détails", {
            "fields": ("description", "old_value", "new_value")
        }),
        ("Métadonnées", {
            "fields": ("created_by", "created_at"),
            "classes": ["collapse"]
        }),
    )


@admin.register(HRDocumentTemplate)
class HRDocumentTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for HRDocumentTemplate."""

    list_display = ["name", "document_type", "is_active", "organization"]
    list_filter = ["organization", "document_type", "is_active"]
    search_fields = ["name"]
    ordering = ["name"]

    fieldsets = (
        (None, {
            "fields": ("organization", "name", "document_type", "is_active")
        }),
        ("Contenu", {
            "fields": ("content", "variables")
        }),
    )
