"""HR URL Configuration."""
from django.urls import path

from . import views

app_name = "hr"

urlpatterns = [
    # Dashboard
    path("", views.HRDashboardView.as_view(), name="dashboard"),

    # Employees
    path("employes/", views.EmployeeListView.as_view(), name="employee_list"),
    path("employes/nouveau/", views.EmployeeCreateView.as_view(), name="employee_create"),
    path("employes/<uuid:pk>/", views.EmployeeDetailView.as_view(), name="employee_detail"),
    path("employes/<uuid:pk>/modifier/", views.EmployeeUpdateView.as_view(), name="employee_update"),
    path("employes/<uuid:pk>/supprimer/", views.EmployeeDeleteView.as_view(), name="employee_delete"),

    # Leaves
    path("conges/", views.LeaveRequestListView.as_view(), name="leave_list"),
    path("conges/demande/", views.LeaveRequestCreateView.as_view(), name="leave_request"),
    path("conges/<uuid:pk>/", views.LeaveRequestDetailView.as_view(), name="leave_detail"),
    path("conges/<uuid:pk>/approuver/", views.leave_approve, name="leave_approve"),
    path("conges/<uuid:pk>/refuser/", views.leave_reject, name="leave_reject"),
    path("conges/calendrier/", views.LeaveCalendarView.as_view(), name="leave_calendar"),
    path("conges/calendrier/events/", views.LeaveCalendarEventsView.as_view(), name="leave_calendar_events"),
    path("conges/soldes/", views.LeaveBalanceView.as_view(), name="leave_balance"),

    # Leave Types
    path("conges/types/", views.LeaveTypeListView.as_view(), name="leave_type_list"),
    path("conges/types/nouveau/", views.LeaveTypeCreateView.as_view(), name="leave_type_create"),
    path("conges/types/<uuid:pk>/modifier/", views.LeaveTypeUpdateView.as_view(), name="leave_type_update"),

    # Timesheets
    path("temps/", views.TimesheetView.as_view(), name="timesheet"),
    path("temps/pointage/", views.attendance_clock, name="attendance_clock"),
    path("temps/recap/", views.TimesheetSummaryView.as_view(), name="timesheet_summary"),

    # Documents
    path("documents/", views.HRDocumentListView.as_view(), name="document_list"),
    path("documents/upload/", views.HRDocumentUploadView.as_view(), name="document_upload"),

    # Departments
    path("departements/", views.DepartmentListView.as_view(), name="department_list"),
    path("departements/nouveau/", views.DepartmentCreateView.as_view(), name="department_create"),
    path("departements/<uuid:pk>/modifier/", views.DepartmentUpdateView.as_view(), name="department_update"),

    # HTMX Partials
    path("partials/employes/", views.EmployeeListPartialView.as_view(), name="employee_list_partial"),
    path("partials/conges/", views.LeaveListPartialView.as_view(), name="leave_list_partial"),
    path("partials/calcul-jours/", views.calculate_leave_days, name="calculate_leave_days"),
]
