"""
Core views.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import UpdateView, ListView, DetailView

from .forms import OrganizationSettingsForm, AssignAdminForm, OrganizationCreateForm
from .models import Organization, OrganizationMembership


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """Health check endpoint for monitoring."""
    return JsonResponse({"status": "ok"})


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    """Home page - redirects to dashboard if authenticated."""
    if request.user.is_authenticated:
        return redirect("dashboard:index")
    return render(request, "core/home.html")


@login_required
def no_organization(request: HttpRequest) -> HttpResponse:
    """Page shown when user has no organization."""
    return render(request, "core/no_organization.html")


class OrganizationSettingsView(LoginRequiredMixin, UpdateView):
    """Organization settings page."""

    model = Organization
    form_class = OrganizationSettingsForm
    template_name = "core/settings.html"

    def get_object(self, queryset=None):
        """Return the current user's organization."""
        return getattr(self.request, "organization", None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document_templates"] = [
            {
                "id": "classic",
                "name": "Classique",
                "description": "Style professionnel traditionnel",
                "preview_class": "bg-blue-500",
            },
            {
                "id": "modern",
                "name": "Moderne",
                "description": "Design épuré avec dégradé",
                "preview_class": "bg-gradient-to-r from-blue-500 to-blue-700",
            },
            {
                "id": "minimal",
                "name": "Minimaliste",
                "description": "Sobre, noir et blanc",
                "preview_class": "bg-gray-800",
            },
            {
                "id": "elegant",
                "name": "Élégant",
                "description": "Style raffiné avec serif",
                "preview_class": "bg-amber-600",
            },
        ]
        return context

    def form_valid(self, form):
        messages.success(self.request, "Paramètres enregistrés avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.path


@login_required
@require_POST
def switch_organization(request: HttpRequest) -> HttpResponse:
    """Switch the user's active organization (super admin only)."""
    # Only super admins can switch organizations
    if not getattr(request.user, 'is_super_admin', False):
        messages.error(request, "Accès réservé aux super administrateurs.")
        return redirect("dashboard:index")

    organization_id = request.POST.get("organization_id")

    if not organization_id:
        messages.error(request, "Entreprise non spécifiée.")
        return redirect(request.META.get("HTTP_REFERER", "dashboard:index"))

    try:
        organization = Organization.objects.get(pk=organization_id)
    except Organization.DoesNotExist:
        messages.error(request, "Entreprise introuvable.")
        return redirect(request.META.get("HTTP_REFERER", "dashboard:index"))

    if request.user.switch_organization(organization):
        messages.success(request, f"Vous êtes maintenant sur {organization.name}.")
    else:
        messages.error(request, "Vous n'avez pas accès à cette entreprise.")

    # Redirect to next URL or dashboard
    next_url = request.POST.get("next", request.META.get("HTTP_REFERER"))
    return redirect(next_url or "dashboard:index")


class SuperAdminRequiredMixin:
    """Mixin that requires the user to be a super admin."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect("accounts:login")
        if not getattr(request.user, 'is_super_admin', False):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Accès réservé aux super administrateurs.")
        return super().dispatch(request, *args, **kwargs)


class OrganizationListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    """List all organizations (super admin only)."""
    model = Organization
    template_name = "core/organization_list.html"
    context_object_name = "organizations"

    def get_queryset(self):
        # Super admin sees all organizations
        return Organization.objects.filter(is_active=True).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_organization"] = getattr(self.request, "organization", None)

        # Get admins for each organization
        org_admins = {}
        for org in context["organizations"]:
            admin_membership = OrganizationMembership.objects.filter(
                organization=org,
                role__in=[OrganizationMembership.Role.OWNER, OrganizationMembership.Role.ADMIN],
                is_active=True
            ).select_related('user').first()
            org_admins[org.pk] = admin_membership.user if admin_membership else None
        context["org_admins"] = org_admins
        return context


class OrganizationDetailView(LoginRequiredMixin, SuperAdminRequiredMixin, DetailView):
    """Detail view for an organization (super admin only)."""
    model = Organization
    template_name = "core/organization_detail.html"
    context_object_name = "organization"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_object()

        # Get all memberships for this organization
        context["memberships"] = OrganizationMembership.objects.filter(
            organization=org,
            is_active=True
        ).select_related('user').order_by('-role', 'user__email')

        # Get admin
        admin_membership = OrganizationMembership.objects.filter(
            organization=org,
            role__in=[OrganizationMembership.Role.OWNER, OrganizationMembership.Role.ADMIN],
            is_active=True
        ).select_related('user').first()
        context["current_admin"] = admin_membership.user if admin_membership else None

        # Form for assigning admin
        context["assign_form"] = AssignAdminForm(organization=org)

        return context


@login_required
@require_POST
def assign_admin(request: HttpRequest, pk) -> HttpResponse:
    """Assign an admin to an organization (super admin only)."""
    if not getattr(request.user, 'is_super_admin', False):
        messages.error(request, "Accès réservé aux super administrateurs.")
        return redirect("dashboard:index")

    organization = get_object_or_404(Organization, pk=pk)
    form = AssignAdminForm(request.POST, organization=organization)

    if form.is_valid():
        user = form.cleaned_data['user']

        # Remove admin role from current admin(s)
        OrganizationMembership.objects.filter(
            organization=organization,
            role__in=[OrganizationMembership.Role.OWNER, OrganizationMembership.Role.ADMIN]
        ).update(role=OrganizationMembership.Role.MEMBER)

        # Create or update membership for the new admin
        membership, created = OrganizationMembership.objects.get_or_create(
            user=user,
            organization=organization,
            defaults={
                'role': OrganizationMembership.Role.ADMIN,
                'invited_by': request.user,
            }
        )

        if not created:
            membership.role = OrganizationMembership.Role.ADMIN
            membership.is_active = True
            membership.save()

        # Update user's organization and active_organization
        user.organization = organization
        user.active_organization = organization
        user.is_organization_admin = True
        user.save(update_fields=['organization', 'active_organization', 'is_organization_admin'])

        messages.success(request, f"{user.email} est maintenant administrateur de {organization.name}.")
    else:
        for error in form.errors.values():
            messages.error(request, error)

    return redirect("core:organization_detail", pk=pk)


@login_required
@require_POST
def remove_member(request: HttpRequest, pk, user_id) -> HttpResponse:
    """Remove a member from an organization (super admin only)."""
    if not getattr(request.user, 'is_super_admin', False):
        messages.error(request, "Accès réservé aux super administrateurs.")
        return redirect("dashboard:index")

    organization = get_object_or_404(Organization, pk=pk)

    from apps.accounts.models import User
    user = get_object_or_404(User, pk=user_id)

    # Remove membership
    OrganizationMembership.objects.filter(
        organization=organization,
        user=user
    ).delete()

    # Clear user's organization if it matches
    if user.organization == organization:
        user.organization = None
        user.active_organization = None
        user.is_organization_admin = False
        user.save(update_fields=['organization', 'active_organization', 'is_organization_admin'])

    messages.success(request, f"{user.email} a été retiré de {organization.name}.")
    return redirect("core:organization_detail", pk=pk)


@login_required
def create_organization(request: HttpRequest) -> HttpResponse:
    """Create a new organization with admin (super admin only)."""
    if not getattr(request.user, 'is_super_admin', False):
        messages.error(request, "Accès réservé aux super administrateurs.")
        return redirect("dashboard:index")

    from apps.accounts.models import User
    import secrets
    import string

    if request.method == "POST":
        form = OrganizationCreateForm(request.POST)
        if form.is_valid():
            # Create organization
            organization = form.save()

            # Get admin details
            admin_email = form.cleaned_data['admin_email']
            admin_first_name = form.cleaned_data.get('admin_first_name', '')
            admin_last_name = form.cleaned_data.get('admin_last_name', '')

            # Check if user already exists
            admin_user = User.objects.filter(email=admin_email).first()

            # Generate temporary password
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

            if not admin_user:
                # Create new admin user
                admin_user = User.objects.create_user(
                    email=admin_email,
                    password=temp_password,
                    first_name=admin_first_name,
                    last_name=admin_last_name,
                )
                messages.info(
                    request,
                    f"Compte créé pour {admin_email}. Mot de passe temporaire: {temp_password}"
                )
            else:
                messages.info(
                    request,
                    f"L'utilisateur {admin_email} existe déjà et a été assigné comme admin."
                )

            # Set user as organization admin
            admin_user.organization = organization
            admin_user.active_organization = organization
            admin_user.is_organization_admin = True
            admin_user.save(update_fields=['organization', 'active_organization', 'is_organization_admin'])

            # Create membership
            OrganizationMembership.objects.create(
                user=admin_user,
                organization=organization,
                role=OrganizationMembership.Role.ADMIN,
                invited_by=request.user,
            )

            messages.success(
                request,
                f"Entreprise '{organization.name}' créée avec {admin_email} comme administrateur."
            )
            return redirect("core:organization_detail", pk=organization.pk)
    else:
        form = OrganizationCreateForm()

    return render(request, "core/organization_form.html", {
        "form": form,
        "title": "Nouvelle entreprise",
    })


@login_required
def edit_organization(request: HttpRequest, pk) -> HttpResponse:
    """Edit an organization (super admin only)."""
    if not getattr(request.user, 'is_super_admin', False):
        messages.error(request, "Accès réservé aux super administrateurs.")
        return redirect("dashboard:index")

    organization = get_object_or_404(Organization, pk=pk)

    if request.method == "POST":
        form = OrganizationSettingsForm(request.POST, request.FILES, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, f"Entreprise '{organization.name}' mise à jour.")
            return redirect("core:organization_detail", pk=pk)
    else:
        form = OrganizationSettingsForm(instance=organization)

    return render(request, "core/organization_form.html", {
        "form": form,
        "organization": organization,
        "title": f"Modifier {organization.name}",
    })


@login_required
def enter_organization(request: HttpRequest, pk) -> HttpResponse:
    """Enter an organization context to view its data (super admin only)."""
    if not getattr(request.user, 'is_super_admin', False):
        messages.error(request, "Accès réservé aux super administrateurs.")
        return redirect("dashboard:index")

    organization = get_object_or_404(Organization, pk=pk)

    # Set the active organization for the super admin
    request.user.active_organization = organization
    request.user.save(update_fields=['active_organization'])

    messages.info(request, f"Vous consultez maintenant les données de {organization.name}.")
    return redirect("dashboard:index")


@login_required
def exit_organization(request: HttpRequest) -> HttpResponse:
    """Exit organization context and return to global view (super admin only)."""
    if not getattr(request.user, 'is_super_admin', False):
        messages.error(request, "Accès réservé aux super administrateurs.")
        return redirect("dashboard:index")

    # Clear the active organization
    request.user.active_organization = None
    request.user.save(update_fields=['active_organization'])

    messages.info(request, "Retour à la vue globale.")
    return redirect("dashboard:index")


@login_required
@require_POST
def delete_organization(request: HttpRequest, pk) -> HttpResponse:
    """Delete an organization (super admin only)."""
    if not getattr(request.user, 'is_super_admin', False):
        messages.error(request, "Accès réservé aux super administrateurs.")
        return redirect("dashboard:index")

    organization = get_object_or_404(Organization, pk=pk)
    org_name = organization.name

    # Check if super admin is currently in this organization
    if request.user.active_organization == organization:
        request.user.active_organization = None
        request.user.save(update_fields=['active_organization'])

    # Remove all memberships
    OrganizationMembership.objects.filter(organization=organization).delete()

    # Clear organization from all users who have it set
    from apps.accounts.models import User
    User.objects.filter(organization=organization).update(
        organization=None,
        active_organization=None,
        is_organization_admin=False
    )
    User.objects.filter(active_organization=organization).update(
        active_organization=None
    )

    # Delete the organization
    organization.delete()

    messages.success(request, f"L'entreprise '{org_name}' a été supprimée.")
    return redirect("core:organization_list")
