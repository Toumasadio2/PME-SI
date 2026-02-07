"""
Core URL configuration.
"""
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health_check, name="health"),
    path("no-organization/", views.no_organization, name="no_organization"),
    path("parametres/", views.OrganizationSettingsView.as_view(), name="settings"),

    # Organization management (super admin)
    path("entreprises/", views.OrganizationListView.as_view(), name="organization_list"),
    path("entreprises/nouvelle/", views.create_organization, name="organization_create"),
    path("entreprises/<uuid:pk>/", views.OrganizationDetailView.as_view(), name="organization_detail"),
    path("entreprises/<uuid:pk>/modifier/", views.edit_organization, name="organization_edit"),
    path("entreprises/<uuid:pk>/entrer/", views.enter_organization, name="organization_enter"),
    path("entreprises/<uuid:pk>/assigner-admin/", views.assign_admin, name="assign_admin"),
    path("entreprises/<uuid:pk>/retirer-membre/<uuid:user_id>/", views.remove_member, name="remove_member"),
    path("sortir-entreprise/", views.exit_organization, name="organization_exit"),

    # Legacy
    path("changer-entreprise/", views.switch_organization, name="switch_organization"),
]
