"""CRM Admin configuration."""
from django.contrib import admin

from .models import (
    Activity,
    Company,
    Contact,
    Document,
    Opportunity,
    PipelineStage,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "color", "organization"]
    list_filter = ["organization"]
    search_fields = ["name"]


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "probability", "is_won", "is_lost", "organization"]
    list_filter = ["organization", "is_won", "is_lost"]
    list_editable = ["order", "probability"]
    ordering = ["organization", "order"]


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0
    fields = ["first_name", "last_name", "email", "phone", "job_title"]
    show_change_link = True


class OpportunityInline(admin.TabularInline):
    model = Opportunity
    extra = 0
    fields = ["name", "stage", "amount", "probability", "expected_close_date"]
    show_change_link = True


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        "name", "category", "city", "phone", "email",
        "contacts_count", "opportunities_count", "organization"
    ]
    list_filter = ["category", "organization", "created_at"]
    search_fields = ["name", "siret", "email", "city"]
    filter_horizontal = ["tags"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [ContactInline, OpportunityInline]

    fieldsets = (
        (None, {
            "fields": ("id", "name", "category", "organization")
        }),
        ("Informations légales", {
            "fields": ("siret", "vat_number"),
            "classes": ("collapse",)
        }),
        ("Adresse", {
            "fields": ("address", "postal_code", "city", "country")
        }),
        ("Contact", {
            "fields": ("phone", "email", "website")
        }),
        ("Informations commerciales", {
            "fields": ("industry", "employees_count", "annual_revenue", "assigned_to")
        }),
        ("Tags et notes", {
            "fields": ("tags", "notes")
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def contacts_count(self, obj):
        return obj.contacts_count
    contacts_count.short_description = "Contacts"

    def opportunities_count(self, obj):
        return obj.opportunities_count
    opportunities_count.short_description = "Opportunités"


class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 0
    fields = ["activity_type", "subject", "status", "scheduled_date"]
    show_change_link = True


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [
        "full_name", "company", "job_title", "email", "phone",
        "category", "assigned_to", "organization"
    ]
    list_filter = ["category", "organization", "company", "created_at"]
    search_fields = ["first_name", "last_name", "email", "company__name"]
    filter_horizontal = ["tags"]
    readonly_fields = ["id", "created_at", "updated_at", "last_activity_date"]
    autocomplete_fields = ["company", "assigned_to"]
    inlines = [ActivityInline]

    fieldsets = (
        (None, {
            "fields": ("id", "civility", "first_name", "last_name", "organization")
        }),
        ("Entreprise", {
            "fields": ("company", "job_title", "department")
        }),
        ("Contact", {
            "fields": ("email", "phone", "mobile")
        }),
        ("Adresse", {
            "fields": ("address", "postal_code", "city", "country"),
            "classes": ("collapse",)
        }),
        ("Classification", {
            "fields": ("category", "tags", "assigned_to")
        }),
        ("Préférences", {
            "fields": ("accepts_marketing", "preferred_contact_method"),
            "classes": ("collapse",)
        }),
        ("Notes", {
            "fields": ("notes",)
        }),
        ("Métadonnées", {
            "fields": ("last_activity_date", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = "Nom complet"


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = [
        "name", "company", "stage", "amount", "probability",
        "weighted_amount", "expected_close_date", "assigned_to", "organization"
    ]
    list_filter = ["stage", "priority", "organization", "created_at", "assigned_to"]
    search_fields = ["name", "company__name", "contact__first_name", "contact__last_name"]
    readonly_fields = ["id", "created_at", "updated_at", "weighted_amount"]
    autocomplete_fields = ["company", "contact", "assigned_to"]
    date_hierarchy = "expected_close_date"
    inlines = [ActivityInline]

    fieldsets = (
        (None, {
            "fields": ("id", "name", "organization")
        }),
        ("Relations", {
            "fields": ("company", "contact")
        }),
        ("Pipeline", {
            "fields": ("stage", "probability", "priority")
        }),
        ("Financier", {
            "fields": ("amount", "weighted_amount")
        }),
        ("Dates", {
            "fields": ("expected_close_date", "closed_date")
        }),
        ("Détails", {
            "fields": ("source", "description", "next_step", "assigned_to")
        }),
        ("Clôture", {
            "fields": ("lost_reason",),
            "classes": ("collapse",)
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def weighted_amount(self, obj):
        return f"{obj.weighted_amount:.2f} €"
    weighted_amount.short_description = "Montant pondéré"


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        "subject", "activity_type", "status", "contact", "company",
        "opportunity", "scheduled_date", "assigned_to", "organization"
    ]
    list_filter = ["activity_type", "status", "organization", "scheduled_date"]
    search_fields = [
        "subject", "description",
        "contact__first_name", "contact__last_name",
        "company__name", "opportunity__name"
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["contact", "company", "opportunity", "assigned_to"]
    date_hierarchy = "scheduled_date"

    fieldsets = (
        (None, {
            "fields": ("id", "activity_type", "status", "organization")
        }),
        ("Contenu", {
            "fields": ("subject", "description")
        }),
        ("Relations", {
            "fields": ("contact", "company", "opportunity")
        }),
        ("Planification", {
            "fields": ("scheduled_date", "completed_date", "duration_minutes", "reminder_date")
        }),
        ("Assignation", {
            "fields": ("assigned_to",)
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "name", "contact", "company", "opportunity",
        "uploaded_by", "created_at", "organization"
    ]
    list_filter = ["organization", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at", "file_extension", "file_size"]
    autocomplete_fields = ["contact", "company", "opportunity", "uploaded_by"]
