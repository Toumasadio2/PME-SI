"""
Search URL configuration.
"""
from django.urls import path

from . import views

app_name = "search"

urlpatterns = [
    path("", views.global_search, name="global"),
    path("suggestions/", views.search_suggestions, name="suggestions"),
]
