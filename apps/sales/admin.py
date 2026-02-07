from django.contrib import admin
from .models import SalesTarget, SalesKPI


@admin.register(SalesTarget)
class SalesTargetAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'target_type', 'period', 'year', 'target_value', 'is_active']
    list_filter = ['organization', 'target_type', 'period', 'year', 'is_active']
    search_fields = ['name']
    ordering = ['-year', '-month', '-quarter']


@admin.register(SalesKPI)
class SalesKPIAdmin(admin.ModelAdmin):
    list_display = ['organization', 'kpi_type', 'date', 'value']
    list_filter = ['organization', 'kpi_type', 'date']
    ordering = ['-date']
    date_hierarchy = 'date'
