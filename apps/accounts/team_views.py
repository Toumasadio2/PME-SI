"""
Team management views.
"""
import secrets
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View

from apps.permissions.models import Permission, Role, UserRole

from .emails import InvitationEmailService
from .forms import InviteMemberForm, UserRoleForm
from .models import User, UserInvitation


class OrganizationAdminRequiredMixin:
    """Mixin that requires user to be organization admin."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not request.user.is_organization_admin and not request.user.is_superuser:
            return HttpResponseForbidden("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)


class TeamListView(LoginRequiredMixin, OrganizationAdminRequiredMixin, ListView):
    """List all team members."""

    model = User
    template_name = "accounts/team/list.html"
    context_object_name = "members"

    def get_queryset(self):
        org = getattr(self.request, "organization", None)
        if not org:
            return User.objects.none()
        return User.objects.filter(organization=org).select_related("organization")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = getattr(self.request, "organization", None)

        # Pending invitations
        if org:
            context["pending_invitations"] = UserInvitation.objects.filter(
                organization=org,
                status=UserInvitation.Status.PENDING,
                expires_at__gt=timezone.now()
            ).order_by("-created_at")

        # Available roles
        context["roles"] = Role.objects.filter(
            Q(organization=org) | Q(organization__isnull=True, is_system=True)
        )

        return context


class InviteMemberView(LoginRequiredMixin, OrganizationAdminRequiredMixin, View):
    """Invite a new team member."""

    template_name = "accounts/team/invite.html"

    def get(self, request):
        org = getattr(request, "organization", None)
        form = InviteMemberForm(organization=org)
        return self._render(request, form)

    def post(self, request):
        org = getattr(request, "organization", None)
        form = InviteMemberForm(request.POST, organization=org)

        if not org:
            messages.error(request, "Entreprise non trouvée.")
            return redirect("accounts:team_list")

        if form.is_valid():
            email = form.cleaned_data["email"]

            # Check if user already exists in organization
            if User.objects.filter(email=email, organization=org).exists():
                messages.warning(request, f"{email} fait déjà partie de l'équipe.")
                return redirect("accounts:team_list")

            # Check for pending invitation
            if UserInvitation.objects.filter(
                email=email,
                organization=org,
                status=UserInvitation.Status.PENDING,
                expires_at__gt=timezone.now()
            ).exists():
                messages.warning(request, f"Une invitation est déjà en attente pour {email}.")
                return redirect("accounts:team_list")

            # Create invitation
            role = form.cleaned_data.get("role")
            invitation = UserInvitation.objects.create(
                email=email,
                organization=org,
                invited_by=request.user,
                role=role.name if role else "user",
                token=secrets.token_urlsafe(32),
                expires_at=timezone.now() + timedelta(days=7),
            )

            # Send invitation email
            try:
                InvitationEmailService.send_invitation(invitation, request)
                messages.success(
                    request,
                    f"Invitation envoyée à {email}. Elle expire dans 7 jours."
                )
            except Exception as e:
                messages.warning(
                    request,
                    f"Invitation créée mais l'email n'a pas pu être envoyé : {str(e)}"
                )

            return redirect("accounts:team_list")

        return self._render(request, form)

    def _render(self, request, form):
        from django.shortcuts import render
        return render(request, self.template_name, {"form": form})


class CancelInvitationView(LoginRequiredMixin, OrganizationAdminRequiredMixin, View):
    """Cancel a pending invitation."""

    def post(self, request, pk):
        org = getattr(request, "organization", None)
        invitation = get_object_or_404(
            UserInvitation,
            pk=pk,
            organization=org,
            status=UserInvitation.Status.PENDING
        )
        invitation.status = UserInvitation.Status.CANCELLED
        invitation.save(update_fields=["status"])
        messages.success(request, "Invitation annulée.")
        return redirect("accounts:team_list")


class UpdateMemberRoleView(LoginRequiredMixin, OrganizationAdminRequiredMixin, View):
    """Update a team member's role."""

    template_name = "accounts/team/edit_role.html"

    def get_member(self, request, pk):
        org = getattr(request, "organization", None)
        if not org:
            return None
        return get_object_or_404(User, pk=pk, organization=org)

    def get(self, request, pk):
        member = self.get_member(request, pk)
        if not member:
            messages.error(request, "Membre non trouvé.")
            return redirect("accounts:team_list")

        org = getattr(request, "organization", None)
        form = UserRoleForm(organization=org, instance=member)
        return self._render(request, form, member, org)

    def post(self, request, pk):
        member = self.get_member(request, pk)
        if not member:
            messages.error(request, "Membre non trouvé.")
            return redirect("accounts:team_list")

        org = getattr(request, "organization", None)
        form = UserRoleForm(request.POST, organization=org, instance=member)

        if form.is_valid():
            # Update organization admin status
            member.is_organization_admin = form.cleaned_data.get("is_organization_admin", False)
            member.save(update_fields=["is_organization_admin"])

            # Update roles
            selected_roles = form.cleaned_data.get("roles", [])

            # Remove existing roles
            UserRole.objects.filter(user=member, organization=org).delete()

            # Add new roles
            for role in selected_roles:
                UserRole.objects.create(user=member, role=role, organization=org)

            messages.success(request, f"Rôle de {member.full_name} mis à jour.")
            return redirect("accounts:team_list")

        return self._render(request, form, member, org)

    def _render(self, request, form, member, org):
        from django.shortcuts import render
        current_roles = UserRole.objects.filter(
            user=member,
            organization=org
        ).select_related("role")
        return render(request, self.template_name, {
            "form": form,
            "member": member,
            "current_roles": current_roles,
        })


class RemoveMemberView(LoginRequiredMixin, OrganizationAdminRequiredMixin, View):
    """Remove a member from the organization."""

    def post(self, request, pk):
        org = getattr(request, "organization", None)
        member = get_object_or_404(User, pk=pk, organization=org)

        # Cannot remove yourself
        if member == request.user:
            messages.error(request, "Vous ne pouvez pas vous retirer vous-même.")
            return redirect("accounts:team_list")

        # Remove from organization
        member.organization = None
        member.is_organization_admin = False
        member.save(update_fields=["organization", "is_organization_admin"])

        # Remove role assignments
        UserRole.objects.filter(user=member, organization=org).delete()

        messages.success(request, f"{member.full_name} a été retiré de l'équipe.")
        return redirect("accounts:team_list")


class RoleListView(LoginRequiredMixin, OrganizationAdminRequiredMixin, ListView):
    """List and manage roles."""

    model = Role
    template_name = "accounts/team/roles.html"
    context_object_name = "roles"

    def get_queryset(self):
        org = getattr(self.request, "organization", None)
        return Role.objects.filter(
            Q(organization=org) | Q(organization__isnull=True, is_system=True)
        ).prefetch_related("permissions")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["modules"] = Permission.Module.choices
        context["actions"] = Permission.Action.choices
        context["all_permissions"] = Permission.objects.all().order_by("module", "action")
        return context


class AcceptInvitationView(View):
    """Accept an invitation to join an organization."""

    template_name = "accounts/team/accept_invitation.html"

    def get(self, request, token):
        from django.shortcuts import render

        invitation = get_object_or_404(
            UserInvitation,
            token=token,
            status=UserInvitation.Status.PENDING,
        )

        # Check if invitation has expired
        if invitation.is_expired:
            invitation.status = UserInvitation.Status.EXPIRED
            invitation.save(update_fields=["status"])
            messages.error(request, "Cette invitation a expiré.")
            return redirect("accounts:login")

        # If user is already logged in
        if request.user.is_authenticated:
            # Check if user email matches invitation
            if request.user.email == invitation.email:
                # Accept invitation directly
                return self._accept_invitation(request, invitation, request.user)
            else:
                messages.warning(
                    request,
                    f"Cette invitation est destinée à {invitation.email}. "
                    f"Déconnectez-vous et reconnectez-vous avec le bon compte."
                )
                return redirect("dashboard:index")

        # Show invitation details
        return render(request, self.template_name, {
            "invitation": invitation,
            "organization": invitation.organization,
        })

    def post(self, request, token):
        invitation = get_object_or_404(
            UserInvitation,
            token=token,
            status=UserInvitation.Status.PENDING,
        )

        if invitation.is_expired:
            invitation.status = UserInvitation.Status.EXPIRED
            invitation.save(update_fields=["status"])
            messages.error(request, "Cette invitation a expiré.")
            return redirect("accounts:login")

        # Check if user already exists
        try:
            user = User.objects.get(email=invitation.email)
            # User exists - they need to login
            messages.info(
                request,
                "Un compte existe déjà avec cette adresse email. Connectez-vous pour accepter l'invitation."
            )
            # Store invitation token in session
            request.session["pending_invitation"] = token
            return redirect("accounts:login")
        except User.DoesNotExist:
            pass

        # Create new user from form data
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")

        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Creating user: email={invitation.email}, password_length={len(password) if password else 0}")

        if not password or password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect("accounts:accept_invitation", token=token)

        if len(password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            return redirect("accounts:accept_invitation", token=token)

        # Create the user
        user = User.objects.create_user(
            email=invitation.email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )

        # Verify password was set correctly
        logger.info(f"User created: {user.email}, has_usable_password={user.has_usable_password()}")

        # Mark email as verified for allauth (user was invited via email)
        try:
            from allauth.account.models import EmailAddress
            EmailAddress.objects.create(
                user=user,
                email=invitation.email,
                verified=True,
                primary=True,
            )
        except Exception:
            pass  # Allauth might not be fully configured

        return self._accept_invitation(request, invitation, user)

    def _accept_invitation(self, request, invitation, user):
        from django.contrib.auth import login

        # Add user to organization
        user.organization = invitation.organization
        user.save(update_fields=["organization"])

        # Mark invitation as accepted
        invitation.accept(user)

        # Assign role if specified
        role_name = invitation.role
        if role_name:
            role = Role.objects.filter(
                Q(name=role_name, organization=invitation.organization) |
                Q(name=role_name, is_system=True)
            ).first()
            if role:
                UserRole.objects.get_or_create(
                    user=user,
                    role=role,
                    organization=invitation.organization,
                )

        # Log user in if not already
        if not request.user.is_authenticated:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        messages.success(
            request,
            f"Bienvenue chez {invitation.organization.name} !"
        )
        return redirect("dashboard:index")
