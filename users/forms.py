from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from fleet.models import Driver, ExpenseLog, FuelLog, MaintenanceLog, RevenueLog, Trip, Vehicle

from .models import AppSettings, CustomUser


class SignUpForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "Enter email address"}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Enter first name"}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Enter last name"}))
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    username = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "password1", "password2", "role")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.username = user.email.split("@")[0]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "registration_number",
            "make",
            "model",
            "vehicle_type",
            "status",
            "cargo_capacity",
            "odometer",
            "acquisition_cost",
        ]
        labels = {
            "registration_number": "Registration No.",
            "cargo_capacity": "Capacity (kg)",
            "odometer": "Odometer Reading (km)",
            "acquisition_cost": "Acquisition Cost",
            "status": "Initial Status",
        }
        widgets = {
            "registration_number": forms.TextInput(attrs={"placeholder": "e.g. MH-01-AB-1234"}),
            "make": forms.TextInput(attrs={"placeholder": "e.g. Tata"}),
            "model": forms.TextInput(attrs={"placeholder": "e.g. Ace Gold"}),
            "cargo_capacity": forms.NumberInput(attrs={"placeholder": "e.g. 1500"}),
            "odometer": forms.NumberInput(attrs={"placeholder": "e.g. 12500"}),
            "acquisition_cost": forms.NumberInput(attrs={"placeholder": "e.g. 9500"}),
        }

    def clean_registration_number(self):
        return self.cleaned_data["registration_number"].strip().upper()


class DriverForm(forms.ModelForm):
    full_name = forms.CharField(
        label="Full Name", widget=forms.TextInput(attrs={"placeholder": "e.g. Rajiv Sharma"})
    )

    class Meta:
        model = Driver
        fields = ["employee_id", "license_number", "license_expiry_date", "assigned_vehicle", "status"]
        labels = {
            "employee_id": "Employee ID",
            "license_number": "License No.",
            "license_expiry_date": "License Expiry",
            "assigned_vehicle": "Assigned Vehicle",
        }
        widgets = {
            "employee_id": forms.TextInput(attrs={"placeholder": "e.g. DR-106"}),
            "license_number": forms.TextInput(attrs={"placeholder": "e.g. MH-01-2020-11111"}),
            "license_expiry_date": forms.DateInput(attrs={"type": "date"}),
        }

    field_order = ["employee_id", "full_name", "license_number", "license_expiry_date", "assigned_vehicle", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_vehicle"].queryset = Vehicle.objects.exclude(status="retired").order_by(
            "registration_number"
        )
        self.fields["assigned_vehicle"].required = False
        self.fields["assigned_vehicle"].empty_label = "--"

    def clean_employee_id(self):
        return self.cleaned_data["employee_id"].strip().upper()

    def clean_license_number(self):
        return self.cleaned_data["license_number"].strip().upper()

    def save(self, commit=True):
        driver = super().save(commit=False)
        parts = self.cleaned_data["full_name"].strip().split(" ", 1)
        driver.first_name = parts[0]
        driver.last_name = parts[1] if len(parts) > 1 else ""
        if commit:
            driver.save()
        return driver


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ["origin", "destination", "vehicle", "driver", "cargo_weight", "planned_distance_km"]
        labels = {
            "origin": "Source",
            "destination": "Destination",
            "cargo_weight": "Cargo Weight (kg)",
            "planned_distance_km": "Planned Distance (km)",
        }
        widgets = {
            "origin": forms.TextInput(attrs={"placeholder": "e.g. Mumbai"}),
            "destination": forms.TextInput(attrs={"placeholder": "e.g. Pune"}),
            "cargo_weight": forms.NumberInput(attrs={"placeholder": "e.g. 500"}),
            "planned_distance_km": forms.NumberInput(attrs={"placeholder": "e.g. 150"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].queryset = Vehicle.objects.filter(status="available").order_by("registration_number")
        self.fields["driver"].queryset = Driver.objects.filter(status="available").order_by("first_name", "last_name")
        self.fields["vehicle"].empty_label = "Select an available vehicle"
        self.fields["driver"].empty_label = "Select an available driver"


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = ["vehicle", "description", "cost"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "e.g. Brake pad replacement"}),
            "cost": forms.NumberInput(attrs={"placeholder": "e.g. 250"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].queryset = Vehicle.objects.exclude(status="retired").order_by("registration_number")
        self.fields["vehicle"].empty_label = "Select a vehicle"


class FuelLogForm(forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = ["vehicle", "liters", "cost", "date_logged"]
        labels = {"liters": "Liters", "cost": "Cost", "date_logged": "Date"}
        widgets = {
            "liters": forms.NumberInput(attrs={"placeholder": "e.g. 45.5", "step": "0.01"}),
            "cost": forms.NumberInput(attrs={"placeholder": "e.g. 3200", "step": "0.01"}),
            "date_logged": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].queryset = Vehicle.objects.exclude(status="retired").order_by("registration_number")
        self.fields["vehicle"].empty_label = "Select a vehicle"


class ExpenseLogForm(forms.ModelForm):
    class Meta:
        model = ExpenseLog
        fields = ["vehicle", "category", "description", "cost", "date_logged"]
        labels = {"category": "Type", "cost": "Cost", "date_logged": "Date"}
        widgets = {
            "description": forms.TextInput(attrs={"placeholder": "e.g. Mumbai-Pune expressway toll"}),
            "cost": forms.NumberInput(attrs={"placeholder": "e.g. 350", "step": "0.01"}),
            "date_logged": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].queryset = Vehicle.objects.exclude(status="retired").order_by("registration_number")
        self.fields["vehicle"].empty_label = "Select a vehicle"


class RevenueLogForm(forms.ModelForm):
    class Meta:
        model = RevenueLog
        fields = ["vehicle", "amount", "description", "date_logged"]
        labels = {"amount": "Revenue Amount", "date_logged": "Date"}
        widgets = {
            "amount": forms.NumberInput(attrs={"placeholder": "e.g. 5000", "step": "0.01"}),
            "description": forms.TextInput(attrs={"placeholder": "e.g. Trip TR-0004 delivery fee"}),
            "date_logged": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].queryset = Vehicle.objects.exclude(status="retired").order_by("registration_number")
        self.fields["vehicle"].empty_label = "Select a vehicle"


class AppSettingsForm(forms.ModelForm):
    class Meta:
        model = AppSettings
        fields = ["depot_name", "currency", "distance_unit"]
        labels = {
            "depot_name": "Depot Name",
            "currency": "Currency",
            "distance_unit": "Distance Unit",
        }
        widgets = {
            "depot_name": forms.TextInput(attrs={"placeholder": "e.g. Gandhinagar Depot GJ4"}),
            "currency": forms.TextInput(attrs={"placeholder": "e.g. INR (₹)"}),
            "distance_unit": forms.TextInput(attrs={"placeholder": "e.g. Kilometers"}),
        }


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "Enter email address"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}))
    remember_me = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user = authenticate(
                self.request,
                username=email.lower(),
                password=password,
            )
            if self.user is None:
                raise forms.ValidationError("Invalid email or password.")

        return cleaned_data
