from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Dashboard
    path('', views.SalesDashboardView.as_view(), name='dashboard'),

    # API endpoints for charts
    path('api/revenue-chart/', views.RevenueChartAPIView.as_view(), name='revenue_chart_api'),
    path('api/profit-chart/', views.ProfitChartAPIView.as_view(), name='profit_chart_api'),

    # Expenses CRUD
    path('depenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('depenses/nouveau/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('depenses/<int:pk>/modifier/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('depenses/<int:pk>/supprimer/', views.ExpenseDeleteView.as_view(), name='expense_delete'),

    # Targets CRUD
    path('objectifs/', views.SalesTargetListView.as_view(), name='target_list'),
    path('objectifs/nouveau/', views.SalesTargetCreateView.as_view(), name='target_create'),
    path('objectifs/<int:pk>/', views.SalesTargetDetailView.as_view(), name='target_detail'),
    path('objectifs/<int:pk>/modifier/', views.SalesTargetUpdateView.as_view(), name='target_update'),
    path('objectifs/<int:pk>/supprimer/', views.SalesTargetDeleteView.as_view(), name='target_delete'),
]
