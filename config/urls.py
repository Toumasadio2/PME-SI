"""
URL configuration for ABSERVICE project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Disable allauth signup - redirect to login
    path("accounts/signup/", RedirectView.as_view(url="/accounts/login/", permanent=False), name="account_signup"),
    path("accounts/", include("allauth.urls")),
    path("auth/", include("apps.accounts.urls", namespace="accounts")),
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    path("search/", include("apps.search.urls", namespace="search")),
    path("notifications/", include("apps.notifications.urls", namespace="notifications")),
    path("crm/", include("apps.crm.urls", namespace="crm")),
    path("facturation/", include("apps.invoicing.urls", namespace="invoicing")),
    path("ventes/", include("apps.sales.urls", namespace="sales")),
    path("rh/", include("apps.hr.urls", namespace="hr")),
    path("", include("apps.core.urls", namespace="core")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
