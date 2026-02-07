"""CRM URL Configuration."""
from django.urls import path

from . import views

app_name = "crm"

urlpatterns = [
    # Dashboard
    path("", views.CRMDashboardView.as_view(), name="dashboard"),

    # Contacts
    path("contacts/", views.ContactListView.as_view(), name="contact_list"),
    path("contacts/new/", views.ContactCreateView.as_view(), name="contact_create"),
    path("contacts/<uuid:pk>/", views.ContactDetailView.as_view(), name="contact_detail"),
    path("contacts/<uuid:pk>/edit/", views.ContactUpdateView.as_view(), name="contact_update"),
    path("contacts/<uuid:pk>/delete/", views.ContactDeleteView.as_view(), name="contact_delete"),

    # Companies
    path("companies/", views.CompanyListView.as_view(), name="company_list"),
    path("companies/new/", views.CompanyCreateView.as_view(), name="company_create"),
    path("companies/<uuid:pk>/", views.CompanyDetailView.as_view(), name="company_detail"),
    path("companies/<uuid:pk>/edit/", views.CompanyUpdateView.as_view(), name="company_update"),
    path("companies/<uuid:pk>/delete/", views.CompanyDeleteView.as_view(), name="company_delete"),

    # Opportunities
    path("opportunities/", views.OpportunityListView.as_view(), name="opportunity_list"),
    path("opportunities/new/", views.OpportunityCreateView.as_view(), name="opportunity_create"),
    path("opportunities/<uuid:pk>/", views.OpportunityDetailView.as_view(), name="opportunity_detail"),
    path("opportunities/<uuid:pk>/edit/", views.OpportunityUpdateView.as_view(), name="opportunity_update"),
    path("opportunities/<uuid:pk>/delete/", views.OpportunityDeleteView.as_view(), name="opportunity_delete"),
    path("opportunities/<uuid:pk>/move-stage/", views.OpportunityMoveStageView.as_view(), name="opportunity_move_stage"),

    # Pipeline Kanban
    path("pipeline/", views.PipelineKanbanView.as_view(), name="pipeline_kanban"),

    # Calendar
    path("calendar/", views.CalendarView.as_view(), name="calendar"),
    path("api/calendar/events/", views.CalendarEventsAPIView.as_view(), name="calendar_events_api"),

    # Activities
    path("activities/", views.ActivityListView.as_view(), name="activity_list"),
    path("activities/new/", views.ActivityCreateView.as_view(), name="activity_create"),
    path("activities/quick/", views.QuickActivityCreateView.as_view(), name="activity_quick_create"),
    path("activities/<uuid:pk>/complete/", views.ActivityCompleteView.as_view(), name="activity_complete"),

    # Tags
    path("tags/", views.TagListView.as_view(), name="tag_list"),
    path("tags/new/", views.TagCreateView.as_view(), name="tag_create"),
    path("tags/<int:pk>/delete/", views.TagDeleteView.as_view(), name="tag_delete"),

    # Pipeline Stages
    path("stages/", views.PipelineStageListView.as_view(), name="pipeline_stage_list"),
    path("stages/new/", views.PipelineStageCreateView.as_view(), name="pipeline_stage_create"),
    path("stages/<int:pk>/edit/", views.PipelineStageUpdateView.as_view(), name="pipeline_stage_update"),
    path("stages/<int:pk>/delete/", views.PipelineStageDeleteView.as_view(), name="pipeline_stage_delete"),

    # HTMX Partials
    path("partials/contacts/", views.ContactListPartialView.as_view(), name="contact_list_partial"),
    path("partials/companies/", views.CompanyListPartialView.as_view(), name="company_list_partial"),
    path("partials/opportunities/", views.OpportunityListPartialView.as_view(), name="opportunity_list_partial"),
    path("partials/activities/", views.ActivityFeedPartialView.as_view(), name="activity_feed_partial"),
]
