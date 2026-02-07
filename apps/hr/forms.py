"""HR Forms."""
from datetime import timedelta
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Attendance,
    Department,
    Employee,
    HRDocument,
    LeaveRequest,
    LeaveType,
    Position,
    Timesheet,
)
from .services import LeaveService


class DepartmentForm(forms.ModelForm):
    """Form for creating/editing departments."""

    class Meta:
        model = Department
        fields = ["name", "code", "description", "parent", "manager"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Nom du département"
            }),
            "code": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "CODE"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Description..."
            }),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "manager": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        if organization:
            self.fields["parent"].queryset = Department.objects.filter(
                organization=organization
            )
            # Exclude self from parent choices if editing
            if self.instance.pk:
                self.fields["parent"].queryset = self.fields["parent"].queryset.exclude(
                    pk=self.instance.pk
                )


class PositionForm(forms.ModelForm):
    """Form for creating/editing positions."""

    class Meta:
        model = Position
        fields = ["title", "department", "description", "salary_min", "salary_max", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Intitulé du poste"
            }),
            "department": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3
            }),
            "salary_min": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "step": "100",
                "placeholder": "25000"
            }),
            "salary_max": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "step": "100",
                "placeholder": "45000"
            }),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        if organization:
            self.fields["department"].queryset = Department.objects.filter(
                organization=organization
            )

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get("salary_min")
        salary_max = cleaned_data.get("salary_max")

        if salary_min and salary_max and salary_min > salary_max:
            raise ValidationError("Le salaire minimum ne peut pas être supérieur au maximum.")

        return cleaned_data


class EmployeeForm(forms.ModelForm):
    """Form for creating/editing employees."""

    class Meta:
        model = Employee
        fields = [
            # Identity
            "employee_id", "first_name", "last_name", "email",
            "phone", "mobile", "date_of_birth", "gender",
            "social_security_number", "photo",
            # Address
            "address", "postal_code", "city", "country",
            # Professional
            "department", "position", "manager",
            "hire_date", "end_date",
            # Contract
            "contract_type", "work_hours", "salary",
            # Status
            "status", "user",
            # Notes
            "notes",
        ]
        widgets = {
            "employee_id": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "EMP001"
            }),
            "first_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Prénom"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Nom"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-input",
                "placeholder": "email@entreprise.fr"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "+33 1 23 45 67 89"
            }),
            "mobile": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "+33 6 12 34 56 78"
            }),
            "date_of_birth": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date"
            }),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "social_security_number": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "1234567890123"
            }),
            "photo": forms.FileInput(attrs={
                "class": "form-input"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2
            }),
            "postal_code": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "75001"
            }),
            "city": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Paris"
            }),
            "country": forms.TextInput(attrs={
                "class": "form-input"
            }),
            "department": forms.Select(attrs={"class": "form-select"}),
            "position": forms.Select(attrs={"class": "form-select"}),
            "manager": forms.Select(attrs={"class": "form-select"}),
            "hire_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date"
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date"
            }),
            "contract_type": forms.Select(attrs={"class": "form-select"}),
            "work_hours": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "max": 48,
                "step": "0.5"
            }),
            "salary": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "step": "100",
                "placeholder": "35000"
            }),
            "status": forms.Select(attrs={"class": "form-select"}),
            "user": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3
            }),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        if organization:
            self.fields["department"].queryset = Department.objects.filter(
                organization=organization
            )
            self.fields["position"].queryset = Position.objects.filter(
                organization=organization,
                is_active=True
            )
            self.fields["manager"].queryset = Employee.objects.filter(
                organization=organization,
                status=Employee.Status.ACTIVE
            )
            # Exclude self from manager choices if editing
            if self.instance.pk:
                self.fields["manager"].queryset = self.fields["manager"].queryset.exclude(
                    pk=self.instance.pk
                )

    def clean(self):
        cleaned_data = super().clean()
        hire_date = cleaned_data.get("hire_date")
        end_date = cleaned_data.get("end_date")

        if hire_date and end_date and end_date < hire_date:
            raise ValidationError("La date de fin ne peut pas être antérieure à la date d'embauche.")

        return cleaned_data


class EmployeeSearchForm(forms.Form):
    """Form for searching employees."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Rechercher un employé...",
            "hx-get": "",
            "hx-trigger": "keyup changed delay:300ms",
            "hx-target": "#employee-list",
        })
    )
    department = forms.ModelChoiceField(
        required=False,
        queryset=Department.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "Tous statuts")] + list(Employee.Status.choices),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    contract_type = forms.ChoiceField(
        required=False,
        choices=[("", "Tous contrats")] + list(Employee.ContractType.choices),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        if organization:
            self.fields["department"].queryset = Department.objects.filter(
                organization=organization
            )


class LeaveRequestForm(forms.ModelForm):
    """Form for creating leave requests."""

    class Meta:
        model = LeaveRequest
        fields = [
            "leave_type", "start_date", "end_date",
            "start_half_day", "end_half_day", "reason"
        ]
        widgets = {
            "leave_type": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",
                "hx-trigger": "change",
                "hx-get": "",
                "hx-target": "#days-count",
                "hx-include": "[name='end_date'], [name='start_half_day'], [name='end_half_day']"
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",
                "hx-trigger": "change",
                "hx-get": "",
                "hx-target": "#days-count",
                "hx-include": "[name='start_date'], [name='start_half_day'], [name='end_half_day']"
            }),
            "start_half_day": forms.CheckboxInput(attrs={
                "class": "form-checkbox",
                "hx-trigger": "change",
                "hx-get": "",
                "hx-target": "#days-count",
                "hx-include": "[name='start_date'], [name='end_date'], [name='end_half_day']"
            }),
            "end_half_day": forms.CheckboxInput(attrs={
                "class": "form-checkbox",
                "hx-trigger": "change",
                "hx-get": "",
                "hx-target": "#days-count",
                "hx-include": "[name='start_date'], [name='end_date'], [name='start_half_day']"
            }),
            "reason": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Motif de la demande..."
            }),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        employee = kwargs.pop("employee", None)
        super().__init__(*args, **kwargs)

        if organization:
            self.fields["leave_type"].queryset = LeaveType.objects.filter(
                organization=organization,
                is_active=True
            )

        self.employee = employee

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        leave_type = cleaned_data.get("leave_type")
        start_half_day = cleaned_data.get("start_half_day", False)
        end_half_day = cleaned_data.get("end_half_day", False)

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError("La date de fin ne peut pas être antérieure à la date de début.")

            # Calculate days
            days_count = LeaveService.calculate_working_days(
                start_date, end_date, start_half_day, end_half_day
            )
            cleaned_data["days_count"] = days_count

            if days_count <= 0:
                raise ValidationError("La période sélectionnée ne contient aucun jour ouvré.")

            # Check balance if employee is set
            if self.employee and leave_type:
                balance = LeaveService.get_employee_balance(
                    self.employee, leave_type, start_date.year
                )
                if days_count > balance["available"]:
                    raise ValidationError(
                        f"Solde insuffisant. Disponible: {balance['available']} jours, "
                        f"demandé: {days_count} jours."
                    )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.days_count = self.cleaned_data.get("days_count", Decimal("0"))
        if commit:
            instance.save()
        return instance


class LeaveApprovalForm(forms.Form):
    """Form for approving/rejecting leave requests."""

    action = forms.ChoiceField(
        choices=[
            ("approve", "Approuver"),
            ("reject", "Refuser"),
        ],
        widget=forms.RadioSelect(attrs={"class": "form-radio"})
    )
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-textarea",
            "rows": 2,
            "placeholder": "Motif du refus..."
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get("action")
        rejection_reason = cleaned_data.get("rejection_reason")

        if action == "reject" and not rejection_reason:
            raise ValidationError("Veuillez indiquer un motif de refus.")

        return cleaned_data


class TimesheetForm(forms.ModelForm):
    """Form for daily timesheet entry."""

    class Meta:
        model = Timesheet
        fields = ["date", "start_time", "end_time", "break_duration", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date"
            }),
            "start_time": forms.TimeInput(attrs={
                "class": "form-input",
                "type": "time"
            }),
            "end_time": forms.TimeInput(attrs={
                "class": "form-input",
                "type": "time"
            }),
            "break_duration": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "01:00:00"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time:
            # Calculate worked hours
            from .services import TimesheetService
            break_duration = cleaned_data.get("break_duration")
            cleaned_data["worked_hours"] = TimesheetService.calculate_worked_hours(
                start_time, end_time, break_duration
            )

        return cleaned_data


class TimesheetWeekForm(forms.Form):
    """Form for weekly timesheet entry."""

    def __init__(self, *args, **kwargs):
        week_start = kwargs.pop("week_start", None)
        super().__init__(*args, **kwargs)

        if week_start:
            for i in range(7):
                day = week_start + timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")

                self.fields[f"start_{day_str}"] = forms.TimeField(
                    required=False,
                    widget=forms.TimeInput(attrs={
                        "class": "form-input text-sm",
                        "type": "time"
                    })
                )
                self.fields[f"end_{day_str}"] = forms.TimeField(
                    required=False,
                    widget=forms.TimeInput(attrs={
                        "class": "form-input text-sm",
                        "type": "time"
                    })
                )
                self.fields[f"break_{day_str}"] = forms.DurationField(
                    required=False,
                    widget=forms.TextInput(attrs={
                        "class": "form-input text-sm",
                        "placeholder": "01:00"
                    })
                )


class AttendanceClockForm(forms.Form):
    """Form for clocking in/out."""

    action = forms.ChoiceField(
        choices=[
            ("clock_in", "Pointer entrée"),
            ("clock_out", "Pointer sortie"),
        ],
        widget=forms.RadioSelect(attrs={"class": "form-radio"})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Notes (optionnel)"
        })
    )


class HRDocumentUploadForm(forms.ModelForm):
    """Form for uploading HR documents."""

    class Meta:
        model = HRDocument
        fields = [
            "document_type", "title", "file",
            "is_confidential", "valid_from", "valid_until", "notes"
        ]
        widgets = {
            "document_type": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Titre du document"
            }),
            "file": forms.FileInput(attrs={
                "class": "form-input"
            }),
            "is_confidential": forms.CheckboxInput(attrs={
                "class": "form-checkbox"
            }),
            "valid_from": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date"
            }),
            "valid_until": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get("valid_from")
        valid_until = cleaned_data.get("valid_until")

        if valid_from and valid_until and valid_until < valid_from:
            raise ValidationError("La date de fin de validité ne peut pas être antérieure à la date de début.")

        return cleaned_data


class LeaveTypeForm(forms.ModelForm):
    """Form for creating/editing leave types."""

    class Meta:
        model = LeaveType
        fields = [
            "name", "code", "description",
            "is_paid", "requires_approval",
            "max_days_per_year", "accrual_rate",
            "color", "is_active"
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Congés payés"
            }),
            "code": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "CP"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2
            }),
            "is_paid": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
            "requires_approval": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
            "max_days_per_year": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "placeholder": "25"
            }),
            "accrual_rate": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "step": "0.5",
                "placeholder": "2.5"
            }),
            "color": forms.TextInput(attrs={
                "type": "color",
                "class": "form-input h-10 w-20"
            }),
            "is_active": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }
