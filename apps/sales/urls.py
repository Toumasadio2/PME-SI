from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Dashboard
    path('', views.SalesDashboardView.as_view(), name='dashboard'),

    # API endpoints for charts
    path('api/revenue-chart/', views.RevenueChartAPIView.as_view(), name='revenue_chart_api'),
    path('api/quotes-chart/', views.QuotesChartAPIView.as_view(), name='quotes_chart_api'),

    # Targets CRUD
    path('objectifs/', views.SalesTargetListView.as_view(), name='target_list'),
    path('objectifs/nouveau/', views.SalesTargetCreateView.as_view(), name='target_create'),
    path('objectifs/<int:pk>/', views.SalesTargetDetailView.as_view(), name='target_detail'),
    path('objectifs/<int:pk>/modifier/', views.SalesTargetUpdateView.as_view(), name='target_update'),
    path('objectifs/<int:pk>/supprimer/', views.SalesTargetDeleteView.as_view(), name='target_delete'),
]
