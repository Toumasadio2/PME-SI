"""
Dashboard URL configuration.
"""
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),

    # Widget endpoints (for HTMX)
    path("widgets/crm/", views.widget_crm, name="widget_crm"),
    path("widgets/invoicing/", views.widget_invoicing, name="widget_invoicing"),
    path("widgets/sales/", views.widget_sales, name="widget_sales"),
    path("widgets/hr/", views.widget_hr, name="widget_hr"),

    # Activity feed
    path("activity/", views.activity_feed, name="activity_feed"),
]
