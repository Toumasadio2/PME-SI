"""CRM Views."""
import json
from decimal import Decimal
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.permissions.mixins import ModulePermissionMixin, PermissionRequiredMixin

from .forms import (
    ActivityForm,
    CompanyForm,
    CompanySearchForm,
    ContactForm,
    ContactSearchForm,
    OpportunityForm,
    OpportunitySearchForm,
    PipelineStageForm,
    QuickActivityForm,
    TagForm,
)
from .models import Activity, Company, Contact, Document, Opportunity, PipelineStage, Tag


class CRMBaseMixin(LoginRequiredMixin, ModulePermissionMixin):
    """Base mixin for CRM views with tenant filtering and module permission."""

    module_required = "crm"

    def get_queryset(self):
        """Filter by current organization."""
        qs = super().get_queryset()
        if hasattr(self.request, "organization") and self.request.organization:
            return qs.filter(organization=self.request.organization)
        return qs.none()

    def form_valid(self, form):
        """Set organization on save."""
        if hasattr(self.request, "organization") and self.request.organization:
            form.instance.organization = self.request.organization
        return super().form_valid(form)


# =============================================================================
# Dashboard
# =============================================================================

class CRMDashboardView(CRMBaseMixin, TemplateView):
    """CRM Dashboard with KPIs and charts."""

    template_name = "crm/dashboard.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        org = getattr(self.request, "organization", None)

        if not org:
            return context

        # Base querysets
        contacts = Contact.objects.filter(organization=org)
        companies = Company.objects.filter(organization=org)
        opportunities = Opportunity.objects.filter(organization=org)
        activities = Activity.objects.filter(organization=org)

        # Open opportunities (not won/lost)
        stages = PipelineStage.objects.filter(organization=org)
        won_lost_stages = stages.filter(Q(is_won=True) | Q(is_lost=True))
        open_opportunities = opportunities.exclude(stage__in=won_lost_stages)

        # KPIs
        context["contacts_count"] = contacts.count()
        context["companies_count"] = companies.count()
        context["opportunities_count"] = open_opportunities.count()

        # Pipeline value
        pipeline_total = open_opportunities.aggregate(
            total=Sum("amount"),
            weighted=Sum("amount") * Sum("probability") / 100
        )
        context["pipeline_value"] = pipeline_total["total"] or Decimal("0")
        context["pipeline_weighted"] = open_opportunities.aggregate(
            weighted=Sum("amount")
        )["weighted"] or Decimal("0")

        # Won this month
        today = timezone.now().date()
        first_of_month = today.replace(day=1)
        won_stages = stages.filter(is_won=True)
        won_this_month = opportunities.filter(
            stage__in=won_stages,
            closed_date__gte=first_of_month
        )
        context["won_this_month"] = won_this_month.aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")
        context["won_count_month"] = won_this_month.count()

        # Conversion rate
        total_closed = opportunities.filter(
            stage__in=won_lost_stages,
            closed_date__gte=first_of_month
        ).count()
        won_count = won_this_month.count()
        context["conversion_rate"] = (
            round(won_count / total_closed * 100, 1) if total_closed > 0 else 0
        )

        # Recent activities
        context["recent_activities"] = activities.select_related(
            "contact", "company", "opportunity"
        ).order_by("-created_at")[:10]

        # Upcoming activities
        context["upcoming_activities"] = activities.filter(
            status=Activity.Status.PLANNED,
            scheduled_date__gte=timezone.now()
        ).select_related(
            "contact", "company", "opportunity"
        ).order_by("scheduled_date")[:5]

        # Overdue activities
        context["overdue_activities"] = activities.filter(
            status=Activity.Status.PLANNED,
            scheduled_date__lt=timezone.now()
        ).count()

        # Top opportunities
        context["top_opportunities"] = open_opportunities.select_related(
            "company", "stage"
        ).order_by("-amount")[:5]

        # Pipeline by stage (for chart)
        pipeline_by_stage = []
        for stage in stages.filter(is_won=False, is_lost=False).order_by("order"):
            stage_opps = opportunities.filter(stage=stage)
            pipeline_by_stage.append({
                "name": stage.name,
                "count": stage_opps.count(),
                "value": float(stage_opps.aggregate(Sum("amount"))["amount__sum"] or 0),
                "color": stage.color
            })
        context["pipeline_by_stage"] = json.dumps(pipeline_by_stage)

        # Contacts by category (for chart)
        contacts_by_category = []
        for cat_value, cat_label in Contact.Category.choices:
            count = contacts.filter(category=cat_value).count()
            if count > 0:
                contacts_by_category.append({
                    "category": cat_label,
                    "count": count
                })
        context["contacts_by_category"] = json.dumps(contacts_by_category)

        return context


# =============================================================================
# Contacts
# =============================================================================

class ContactListView(CRMBaseMixin, PermissionRequiredMixin, ListView):
    """List all contacts."""

    model = Contact
    template_name = "crm/contact_list.html"
    context_object_name = "contacts"
    paginate_by = 25
    permission_required = "crm_view"

    def get_queryset(self):
        qs = super().get_queryset().select_related("company", "assigned_to")

        # Search
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q) |
                Q(company__name__icontains=q)
            )

        # Category filter
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)

        # Company filter
        company = self.request.GET.get("company")
        if company:
            qs = qs.filter(company_id=company)

        return qs.order_by("last_name", "first_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = ContactSearchForm(
            self.request.GET,
            organization=getattr(self.request, "organization", None)
        )
        context["total_count"] = self.get_queryset().count()
        return context


class ContactDetailView(CRMBaseMixin, PermissionRequiredMixin, DetailView):
    """Contact detail view."""

    model = Contact
    template_name = "crm/contact_detail.html"
    context_object_name = "contact"
    permission_required = "crm_view"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "company", "assigned_to"
        ).prefetch_related("tags", "activities", "opportunities", "documents")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activities"] = self.object.activities.select_related(
            "opportunity"
        ).order_by("-created_at")[:20]
        context["opportunities"] = self.object.opportunities.select_related(
            "stage"
        ).order_by("-created_at")
        context["quick_activity_form"] = QuickActivityForm()
        return context


class ContactCreateView(CRMBaseMixin, PermissionRequiredMixin, CreateView):
    """Create a new contact."""

    model = Contact
    form_class = ContactForm
    template_name = "crm/contact_form.html"
    permission_required = "crm_create"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        org = getattr(self.request, "organization", None)
        if org:
            form.fields["company"].queryset = Company.objects.filter(organization=org)
            form.fields["tags"].queryset = Tag.objects.filter(organization=org)
        return form

    def form_valid(self, form):
        messages.success(self.request, "Contact créé avec succès.")
        return super().form_valid(form)


class ContactUpdateView(CRMBaseMixin, PermissionRequiredMixin, UpdateView):
    """Update a contact."""

    model = Contact
    form_class = ContactForm
    template_name = "crm/contact_form.html"
    permission_required = "crm_edit"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        org = getattr(self.request, "organization", None)
        if org:
            form.fields["company"].queryset = Company.objects.filter(organization=org)
            form.fields["tags"].queryset = Tag.objects.filter(organization=org)
        return form

    def form_valid(self, form):
        messages.success(self.request, "Contact mis à jour avec succès.")
        return super().form_valid(form)


class ContactDeleteView(CRMBaseMixin, PermissionRequiredMixin, DeleteView):
    """Delete a contact."""

    model = Contact
    template_name = "crm/contact_confirm_delete.html"
    success_url = reverse_lazy("crm:contact_list")
    permission_required = "crm_delete"

    def post(self, request, *args, **kwargs):
        messages.success(request, "Contact supprimé avec succès.")
        return super().post(request, *args, **kwargs)


# =============================================================================
# Companies
# =============================================================================

class CompanyListView(CRMBaseMixin, PermissionRequiredMixin, ListView):
    """List all companies."""

    model = Company
    template_name = "crm/company_list.html"
    context_object_name = "companies"
    paginate_by = 25
    permission_required = "crm_view"

    def get_queryset(self):
        qs = super().get_queryset().annotate(
            num_contacts=Count("contacts"),
            num_opportunities=Count("opportunities")
        )

        # Search
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(email__icontains=q) |
                Q(siret__icontains=q) |
                Q(city__icontains=q)
            )

        # Category filter
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)

        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = CompanySearchForm(self.request.GET)
        context["total_count"] = self.get_queryset().count()
        return context


class CompanyDetailView(CRMBaseMixin, PermissionRequiredMixin, DetailView):
    """Company detail view."""

    model = Company
    template_name = "crm/company_detail.html"
    context_object_name = "company"
    permission_required = "crm_view"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "assigned_to"
        ).prefetch_related("tags", "contacts", "opportunities", "activities")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contacts"] = self.object.contacts.all()
        context["opportunities"] = self.object.opportunities.select_related(
            "stage"
        ).order_by("-created_at")
        context["activities"] = self.object.activities.order_by("-created_at")[:20]
        context["quick_activity_form"] = QuickActivityForm()
        return context


class CompanyCreateView(CRMBaseMixin, PermissionRequiredMixin, CreateView):
    """Create a new company - DISABLED."""

    model = Company
    form_class = CompanyForm
    template_name = "crm/company_form.html"
    permission_required = "crm_create"

    def dispatch(self, request, *args, **kwargs):
        """Disable company creation - redirect to list."""
        messages.warning(request, "La création de nouvelles entreprises n'est pas autorisée. Vous pouvez uniquement modifier les entreprises existantes.")
        return redirect("crm:company_list")


class CompanyUpdateView(CRMBaseMixin, PermissionRequiredMixin, UpdateView):
    """Update a company."""

    model = Company
    form_class = CompanyForm
    template_name = "crm/company_form.html"
    permission_required = "crm_edit"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        org = getattr(self.request, "organization", None)
        if org:
            form.fields["tags"].queryset = Tag.objects.filter(organization=org)
        return form

    def form_valid(self, form):
        messages.success(self.request, "Entreprise mise à jour avec succès.")
        return super().form_valid(form)


class CompanyDeleteView(CRMBaseMixin, PermissionRequiredMixin, DeleteView):
    """Delete a company."""

    model = Company
    template_name = "crm/company_confirm_delete.html"
    success_url = reverse_lazy("crm:company_list")
    permission_required = "crm_delete"

    def post(self, request, *args, **kwargs):
        messages.success(request, "Entreprise supprimée avec succès.")
        return super().post(request, *args, **kwargs)


# =============================================================================
# Opportunities
# =============================================================================

class OpportunityListView(CRMBaseMixin, PermissionRequiredMixin, ListView):
    """List all opportunities."""

    model = Opportunity
    template_name = "crm/opportunity_list.html"
    context_object_name = "opportunities"
    paginate_by = 25
    permission_required = "crm_view"

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "company", "contact", "stage", "assigned_to"
        )

        # Search
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(company__name__icontains=q)
            )

        # Stage filter
        stage = self.request.GET.get("stage")
        if stage:
            qs = qs.filter(stage_id=stage)

        # Only open opportunities by default
        show_closed = self.request.GET.get("show_closed")
        if not show_closed:
            qs = qs.filter(stage__is_won=False, stage__is_lost=False)

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = getattr(self.request, "organization", None)
        context["search_form"] = OpportunitySearchForm(
            self.request.GET,
            organization=org
        )
        context["total_count"] = self.get_queryset().count()

        # Totals
        qs = self.get_queryset()
        totals = qs.aggregate(
            total_amount=Sum("amount"),
        )
        context["total_amount"] = totals["total_amount"] or Decimal("0")

        return context


class OpportunityDetailView(CRMBaseMixin, PermissionRequiredMixin, DetailView):
    """Opportunity detail view."""

    model = Opportunity
    template_name = "crm/opportunity_detail.html"
    context_object_name = "opportunity"
    permission_required = "crm_view"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "company", "contact", "stage", "assigned_to"
        ).prefetch_related("activities", "documents")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activities"] = self.object.activities.order_by("-created_at")
        context["stages"] = PipelineStage.objects.filter(
            organization=self.request.organization
        ).order_by("order")
        context["quick_activity_form"] = QuickActivityForm()
        return context


class OpportunityCreateView(CRMBaseMixin, PermissionRequiredMixin, CreateView):
    """Create a new opportunity."""

    model = Opportunity
    form_class = OpportunityForm
    template_name = "crm/opportunity_form.html"
    permission_required = "crm_create"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = getattr(self.request, "organization", None)
        return kwargs

    def form_valid(self, form):
        # Set probability from stage if not set
        if not form.cleaned_data.get("probability"):
            form.instance.probability = form.instance.stage.probability
        messages.success(self.request, "Opportunité créée avec succès.")
        return super().form_valid(form)


class OpportunityUpdateView(CRMBaseMixin, PermissionRequiredMixin, UpdateView):
    """Update an opportunity."""

    model = Opportunity
    form_class = OpportunityForm
    template_name = "crm/opportunity_form.html"
    permission_required = "crm_edit"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = getattr(self.request, "organization", None)
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Opportunité mise à jour avec succès.")
        return super().form_valid(form)


class OpportunityDeleteView(CRMBaseMixin, PermissionRequiredMixin, DeleteView):
    """Delete an opportunity."""

    model = Opportunity
    template_name = "crm/opportunity_confirm_delete.html"
    success_url = reverse_lazy("crm:opportunity_list")
    permission_required = "crm_delete"

    def post(self, request, *args, **kwargs):
        messages.success(request, "Opportunité supprimée avec succès.")
        return super().post(request, *args, **kwargs)


# =============================================================================
# Pipeline Kanban
# =============================================================================

class PipelineKanbanView(CRMBaseMixin, PermissionRequiredMixin, TemplateView):
    """Kanban board view for pipeline."""

    template_name = "crm/pipeline_kanban.html"
    permission_required = "crm_view"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = getattr(self.request, "organization", None)

        if org:
            # Get stages with opportunities
            stages = PipelineStage.objects.filter(
                organization=org
            ).order_by("order")

            pipeline_data = []
            for stage in stages:
                opportunities = Opportunity.objects.filter(
                    organization=org,
                    stage=stage
                ).select_related("company", "contact").order_by("-amount")

                stage_total = opportunities.aggregate(Sum("amount"))["amount__sum"] or 0

                pipeline_data.append({
                    "stage": stage,
                    "opportunities": opportunities,
                    "count": opportunities.count(),
                    "total": stage_total
                })

            context["pipeline_data"] = pipeline_data

            # Totals
            all_opportunities = Opportunity.objects.filter(
                organization=org,
                stage__is_won=False,
                stage__is_lost=False
            )
            context["total_opportunities"] = all_opportunities.count()
            context["total_value"] = all_opportunities.aggregate(
                Sum("amount")
            )["amount__sum"] or 0

        return context


class OpportunityMoveStageView(CRMBaseMixin, PermissionRequiredMixin, View):
    """HTMX view to move opportunity to a new stage."""

    permission_required = "crm_edit"

    def post(self, request, pk):
        org = getattr(request, "organization", None)
        opportunity = get_object_or_404(
            Opportunity,
            pk=pk,
            organization=org
        )

        stage_id = request.POST.get("stage_id")
        if stage_id:
            stage = get_object_or_404(
                PipelineStage,
                pk=stage_id,
                organization=org
            )
            opportunity.move_to_stage(stage)

            # Return updated card HTML
            if request.headers.get("HX-Request"):
                return HttpResponse(status=200)

        return redirect("crm:pipeline_kanban")


# =============================================================================
# Activities
# =============================================================================

class ActivityListView(CRMBaseMixin, PermissionRequiredMixin, ListView):
    """List all activities."""

    model = Activity
    template_name = "crm/activity_list.html"
    context_object_name = "activities"
    paginate_by = 50
    permission_required = "crm_view"

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "contact", "company", "opportunity", "assigned_to"
        )

        # Filter by type
        activity_type = self.request.GET.get("type")
        if activity_type:
            qs = qs.filter(activity_type=activity_type)

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        # Filter upcoming
        upcoming = self.request.GET.get("upcoming")
        if upcoming:
            qs = qs.filter(
                status=Activity.Status.PLANNED,
                scheduled_date__gte=timezone.now()
            )

        return qs.order_by("-scheduled_date", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activity_types"] = Activity.ActivityType.choices
        context["statuses"] = Activity.Status.choices
        return context


class ActivityCreateView(CRMBaseMixin, PermissionRequiredMixin, CreateView):
    """Create a new activity."""

    model = Activity
    form_class = ActivityForm
    template_name = "crm/activity_form.html"
    permission_required = "crm_create"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = getattr(self.request, "organization", None)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()

        # Pre-fill from URL params
        contact_id = self.request.GET.get("contact")
        if contact_id:
            initial["contact"] = contact_id

        company_id = self.request.GET.get("company")
        if company_id:
            initial["company"] = company_id

        opportunity_id = self.request.GET.get("opportunity")
        if opportunity_id:
            initial["opportunity"] = opportunity_id

        return initial

    def form_valid(self, form):
        form.instance.assigned_to = self.request.user

        # If completed, set completed_date
        if form.instance.status == Activity.Status.COMPLETED:
            form.instance.completed_date = timezone.now()

        messages.success(self.request, "Activité créée avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect back to referring page if available
        referer = self.request.GET.get("next")
        if referer:
            return referer
        return reverse_lazy("crm:activity_list")


class QuickActivityCreateView(CRMBaseMixin, View):
    """HTMX view for quick activity logging."""

    def post(self, request):
        form = QuickActivityForm(request.POST)

        if form.is_valid():
            activity = form.save(commit=False)
            activity.organization = request.organization
            activity.assigned_to = request.user
            activity.status = Activity.Status.COMPLETED
            activity.completed_date = timezone.now()

            # Set relations from request
            contact_id = request.POST.get("contact_id")
            if contact_id:
                activity.contact_id = contact_id

            company_id = request.POST.get("company_id")
            if company_id:
                activity.company_id = company_id

            opportunity_id = request.POST.get("opportunity_id")
            if opportunity_id:
                activity.opportunity_id = opportunity_id

            activity.save()

            # Update contact's last activity
            if activity.contact:
                activity.contact.update_last_activity()

            if request.headers.get("HX-Request"):
                # Return updated activity feed
                return HttpResponse(
                    '<div class="text-green-600 text-sm">Activité enregistrée!</div>'
                )

        return redirect(request.META.get("HTTP_REFERER", "/"))


class ActivityCompleteView(CRMBaseMixin, View):
    """Mark activity as completed."""

    def post(self, request, pk):
        activity = get_object_or_404(
            Activity,
            pk=pk,
            organization=request.organization
        )
        activity.complete()

        if request.headers.get("HX-Request"):
            return HttpResponse(status=200)

        messages.success(request, "Activité marquée comme terminée.")
        return redirect(request.META.get("HTTP_REFERER", "crm:activity_list"))


# =============================================================================
# Tags
# =============================================================================

class TagListView(CRMBaseMixin, PermissionRequiredMixin, ListView):
    """List all tags."""

    model = Tag
    template_name = "crm/tag_list.html"
    context_object_name = "tags"
    permission_required = "crm_view"


class TagCreateView(CRMBaseMixin, PermissionRequiredMixin, CreateView):
    """Create a new tag."""

    model = Tag
    form_class = TagForm
    template_name = "crm/tag_form.html"
    success_url = reverse_lazy("crm:tag_list")
    permission_required = "crm_create"

    def form_valid(self, form):
        messages.success(self.request, "Tag créé avec succès.")
        return super().form_valid(form)


class TagDeleteView(CRMBaseMixin, PermissionRequiredMixin, DeleteView):
    """Delete a tag."""

    model = Tag
    template_name = "crm/tag_confirm_delete.html"
    success_url = reverse_lazy("crm:tag_list")
    permission_required = "crm_delete"


# =============================================================================
# Pipeline Stages
# =============================================================================

class PipelineStageListView(CRMBaseMixin, PermissionRequiredMixin, ListView):
    """List all pipeline stages."""

    model = PipelineStage
    template_name = "crm/pipeline_stage_list.html"
    context_object_name = "stages"
    permission_required = "crm_view"


class PipelineStageCreateView(CRMBaseMixin, PermissionRequiredMixin, CreateView):
    """Create a new pipeline stage."""

    model = PipelineStage
    form_class = PipelineStageForm
    template_name = "crm/pipeline_stage_form.html"
    success_url = reverse_lazy("crm:pipeline_stage_list")
    permission_required = "crm_create"


class PipelineStageUpdateView(CRMBaseMixin, PermissionRequiredMixin, UpdateView):
    """Update a pipeline stage."""

    model = PipelineStage
    form_class = PipelineStageForm
    template_name = "crm/pipeline_stage_form.html"
    success_url = reverse_lazy("crm:pipeline_stage_list")
    permission_required = "crm_edit"


class PipelineStageDeleteView(CRMBaseMixin, PermissionRequiredMixin, DeleteView):
    """Delete a pipeline stage."""

    model = PipelineStage
    template_name = "crm/pipeline_stage_confirm_delete.html"
    success_url = reverse_lazy("crm:pipeline_stage_list")
    permission_required = "crm_delete"


# =============================================================================
# HTMX Partial Views
# =============================================================================

class ContactListPartialView(ContactListView):
    """Partial view for HTMX contact list updates."""

    template_name = "crm/partials/contact_list.html"


class CompanyListPartialView(CompanyListView):
    """Partial view for HTMX company list updates."""

    template_name = "crm/partials/company_list.html"


class OpportunityListPartialView(OpportunityListView):
    """Partial view for HTMX opportunity list updates."""

    template_name = "crm/partials/opportunity_list.html"


class ActivityFeedPartialView(CRMBaseMixin, ListView):
    """Partial view for activity feed."""

    model = Activity
    template_name = "crm/partials/activity_feed.html"
    context_object_name = "activities"

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "contact", "company", "opportunity"
        )

        contact_id = self.request.GET.get("contact")
        if contact_id:
            qs = qs.filter(contact_id=contact_id)

        company_id = self.request.GET.get("company")
        if company_id:
            qs = qs.filter(company_id=company_id)

        opportunity_id = self.request.GET.get("opportunity")
        if opportunity_id:
            qs = qs.filter(opportunity_id=opportunity_id)

        return qs.order_by("-created_at")[:20]


# =============================================================================
# Calendar
# =============================================================================

class CalendarView(CRMBaseMixin, TemplateView):
    """Vue calendrier des activités."""
    template_name = "crm/calendar.html"


class CalendarEventsAPIView(CRMBaseMixin, View):
    """API endpoint pour les événements du calendrier (FullCalendar)."""

    def get(self, request, *args, **kwargs):
        org = getattr(request, "organization", None)
        if not org:
            return JsonResponse({"events": []})

        # Get date range from FullCalendar
        start = request.GET.get("start")
        end = request.GET.get("end")

        activities = Activity.objects.filter(
            organization=org,
            scheduled_date__isnull=False
        ).select_related("contact", "company", "opportunity")

        if start:
            activities = activities.filter(scheduled_date__gte=start)
        if end:
            activities = activities.filter(scheduled_date__lte=end)

        # Color mapping by activity type
        colors = {
            "CALL": "#3B82F6",      # blue
            "EMAIL": "#10B981",     # green
            "MEETING": "#8B5CF6",   # purple
            "TASK": "#F59E0B",      # amber
            "NOTE": "#6B7280",      # gray
            "DEMO": "#EC4899",      # pink
            "PROPOSAL": "#14B8A6",  # teal
            "OTHER": "#9CA3AF",     # gray
        }

        events = []
        for activity in activities:
            event = {
                "id": str(activity.id),
                "title": activity.subject,
                "start": activity.scheduled_date.isoformat(),
                "color": colors.get(activity.activity_type, "#6B7280"),
                "extendedProps": {
                    "type": activity.get_activity_type_display(),
                    "status": activity.get_status_display(),
                    "description": activity.description[:100] if activity.description else "",
                    "contact": activity.contact.display_name if activity.contact else None,
                    "company": activity.company.name if activity.company else None,
                }
            }
            # Add duration for meetings
            if activity.duration_minutes:
                from datetime import timedelta
                end_time = activity.scheduled_date + timedelta(minutes=activity.duration_minutes)
                event["end"] = end_time.isoformat()

            # Mark completed/cancelled differently
            if activity.status == "COMPLETED":
                event["classNames"] = ["fc-event-completed"]
            elif activity.status == "CANCELLED":
                event["classNames"] = ["fc-event-cancelled"]

            events.append(event)

        return JsonResponse(events, safe=False)
