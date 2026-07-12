import csv
from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView, View

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from fleet.models import Driver, ExpenseLog, FuelLog, MaintenanceLog, RevenueLog, Trip, Vehicle

from .forms import (
    AppSettingsForm,
    DriverForm,
    ExpenseLogForm,
    FuelLogForm,
    LoginForm,
    MaintenanceForm,
    RevenueLogForm,
    SignUpForm,
    TripForm,
    VehicleForm,
)
from .models import AppSettings, CustomUser, RolePermission

RBAC_MODULES = ("fleet", "drivers", "trips", "fuel", "analytics")
RBAC_ROLES = [choice for choice in CustomUser.ROLE_CHOICES if choice[0] != "admin"]

MONTH_ABBR = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


ROLE_HOME = {
    "admin": "dashboard",
    "fleet_manager": "fleet",
    "dispatcher": "trips",
    "safety_officer": "drivers",
    "financial_analyst": "dashboard",
}

ROLE_NAV = {
    "admin": [
        ("dashboard", "Dashboard"),
        ("fleet", "Fleet"),
        ("drivers", "Drivers"),
        ("trips", "Trips"),
        ("maintenance", "Maintenance"),
        ("fuel", "Fuel & Expenses"),
        ("analytics", "Analytics"),
        ("settings", "Settings"),
    ],
    "fleet_manager": [
        ("fleet", "Fleet"),
        ("drivers", "Drivers"),
        ("trips", "Trips"),
        ("maintenance", "Maintenance"),
        ("fuel", "Fuel & Expenses"),
        ("analytics", "Analytics"),
    ],
    "dispatcher": [
        ("trips", "Trips"),
    ],
    "safety_officer": [
        ("drivers", "Drivers"),
        ("trips", "Trips"),
    ],
    "financial_analyst": [
        ("dashboard", "Dashboard"),
        ("maintenance", "Maintenance"),
        ("fuel", "Fuel & Expenses"),
        ("analytics", "Analytics"),
    ],
}


def role_home_name(role):
    return ROLE_HOME.get(role, "dashboard")


NAV_ICON_SVG = {
    "dashboard": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="3" width="7" height="7" rx="1.5"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1.5"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1.5"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>'
    ),
    "fleet": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M3 7h11v9H3z"/><path d="M14 10h4l3 3v3h-7z"/>'
        '<circle cx="7" cy="18" r="1.8"/><circle cx="17.5" cy="18" r="1.8"/></svg>'
    ),
    "drivers": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="8" r="3.2"/>'
        '<path d="M4.5 20c1.4-3.6 4.2-5.5 7.5-5.5s6.1 1.9 7.5 5.5"/></svg>'
    ),
    "trips": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="6" cy="6" r="2"/><circle cx="18" cy="18" r="2"/>'
        '<path d="M6 8v3a4 4 0 0 0 4 4h4a4 4 0 0 1 4 4"/></svg>'
    ),
    "maintenance": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14.7 6.3a4 4 0 0 0-5.4 4.6L3 17.2V21h3.8l6.3-6.3a4 4 0 0 0 4.6-5.4'
        'l-2.6 2.6-2.4-.6-.6-2.4z"/></svg>'
    ),
    "fuel": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 21V5a2 2 0 0 1 2-2h5a2 2 0 0 1 2 2v16"/><path d="M4 11h9"/>'
        '<path d="M15 8l3 2v6a1.5 1.5 0 0 0 3 0V9.5L18 6"/><path d="M2 21h14"/></svg>'
    ),
    "analytics": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M2 20h20"/></svg>'
    ),
    "settings": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 13a7.7 7.7 0 0 0 0-2l2-1.4-2-3.4-2.3.8a7.7 7.7 0 0 0-1.7-1L15 4h-4l-.4 2'
        'a7.7 7.7 0 0 0-1.7 1l-2.3-.8-2 3.4L6.6 11a7.7 7.7 0 0 0 0 2l-2 1.4 2 3.4 2.3-.8'
        'a7.7 7.7 0 0 0 1.7 1L11 20h4l.4-2a7.7 7.7 0 0 0 1.7-1l2.3.8 2-3.4z"/></svg>'
    ),
}


def get_role_access(role, module):
    try:
        return RolePermission.objects.get(role=role, module=module).access
    except RolePermission.DoesNotExist:
        return "none"


def role_navigation(role, active):
    items = ROLE_NAV.get(role, ROLE_NAV["dispatcher"])
    access_map = (
        {}
        if role == "admin"
        else {rp.module: rp.access for rp in RolePermission.objects.filter(role=role)}
    )
    result = []
    for name, label in items:
        if role != "admin" and name in RBAC_MODULES and access_map.get(name, "none") == "none":
            continue
        result.append(
            {
                "name": name,
                "label": label,
                "url_name": name,
                "active": name == active,
                "icon": mark_safe(NAV_ICON_SVG.get(name, "")),
            }
        )
    return result


class AuthLandingView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect(role_home_name(request.user.role))
        return redirect("login")


class LoginPageView(View):
    template_name = "users/login.html"

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        form.request = request
        if form.is_valid():
            user = form.user
            login(request, user)
            if not form.cleaned_data.get("remember_me"):
                request.session.set_expiry(0)
            messages.success(request, "Welcome back.")
            return redirect(role_home_name(user.role))
        return render(request, self.template_name, {"form": form})


class SignupPageView(View):
    template_name = "users/signup.html"

    def get(self, request):
        form = SignUpForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please sign in.")
            return redirect("login")
        return render(request, self.template_name, {"form": form})


class LogoutPageView(View):
    def post(self, request):
        logout(request)
        return redirect("login")

    def get(self, request):
        logout(request)
        return redirect("login")


class RoleSectionView(LoginRequiredMixin, TemplateView):
    allowed_roles = ()
    rbac_module = None
    active_page = ""
    page_title = ""
    page_subtitle = ""
    template_name = ""
    login_url = "login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        user = request.user
        if user.is_superuser or user.role == "admin":
            return super().dispatch(request, *args, **kwargs)
        if self.rbac_module:
            access = get_role_access(user.role, self.rbac_module)
            if access == "none":
                return redirect(role_home_name(user.role))
            if access == "view" and request.method not in ("GET", "HEAD"):
                messages.error(request, "You have view-only access to this section.")
                return redirect(request.path)
        elif self.allowed_roles and user.role not in self.allowed_roles:
            return redirect(role_home_name(user.role))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = self.active_page
        context["page_title"] = self.page_title
        context["page_subtitle"] = self.page_subtitle
        context["nav_items"] = role_navigation(self.request.user.role, self.active_page)
        context["role_label"] = self.request.user.get_role_display()
        context["initial"] = (self.request.user.first_name or self.request.user.email[:1]).upper()
        return context


class DashboardView(RoleSectionView):
    template_name = "users/dashboard.html"
    allowed_roles = ("admin", "financial_analyst")
    active_page = "dashboard"
    page_title = "Dashboard"
    page_subtitle = "Real-time overview of fleet operations."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle_type = self.request.GET.get("vehicle_type", "all")
        status = self.request.GET.get("status", "all")
        region = self.request.GET.get("region", "all")

        vehicles = Vehicle.objects.all().order_by("registration_number")
        if vehicle_type != "all":
            vehicles = vehicles.filter(vehicle_type=vehicle_type)
        if status != "all":
            vehicles = vehicles.filter(status=status)
        if region != "all":
            vehicles = vehicles.filter(region=region)

        vehicle_ids = vehicles.values_list("id", flat=True)
        trips = Trip.objects.filter(vehicle_id__in=vehicle_ids).select_related("vehicle", "driver")
        drivers = Driver.objects.filter(trips__vehicle_id__in=vehicle_ids).distinct()

        active_vehicles = vehicles.exclude(status="retired").count()
        available_vehicles = vehicles.filter(status="active").count()
        maintenance_vehicles = vehicles.filter(status="in_shop").count()
        active_trips = trips.filter(status="dispatched").count()
        pending_trips = trips.filter(status="draft").count()
        drivers_on_duty = drivers.filter(status="on_trip").count()
        fleet_utilization = round((active_trips / active_vehicles) * 100) if active_vehicles else 0
        status_max = max(active_vehicles, available_vehicles, maintenance_vehicles, 1)

        context.update(
            {
                "vehicles": vehicles,
                "recent_trips": trips.order_by("-id")[:6],
                "active_vehicles": active_vehicles,
                "available_vehicles": available_vehicles,
                "maintenance_vehicles": maintenance_vehicles,
                "active_trips": active_trips,
                "pending_trips": pending_trips,
                "drivers_on_duty": drivers_on_duty,
                "fleet_utilization": fleet_utilization,
                "vehicle_types": Vehicle.objects.order_by().values_list("vehicle_type", flat=True).distinct(),
                "regions": Vehicle.objects.order_by().values_list("region", flat=True).distinct(),
                "selected_vehicle_type": vehicle_type,
                "selected_status": status,
                "selected_region": region,
                "status_max": status_max,
            }
        )
        return context


class FleetView(RoleSectionView):
    template_name = "users/fleet.html"
    rbac_module = "fleet"
    active_page = "fleet"
    page_title = "Vehicles"
    page_subtitle = "Manage and track company vehicles."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.request.GET.get("status", "all")
        vehicles = Vehicle.objects.all().order_by("registration_number")
        if status != "all":
            vehicles = vehicles.filter(status=status)
        context["vehicles"] = vehicles
        context["status_filter"] = status
        context["status_counts"] = {
            "available": Vehicle.objects.filter(status="active").count(),
            "on_trip": Vehicle.objects.filter(status="on_trip").count(),
            "in_shop": Vehicle.objects.filter(status="in_shop").count(),
            "retired": Vehicle.objects.filter(status="retired").count(),
        }
        context.setdefault("vehicle_form", VehicleForm())
        context.setdefault("duplicate_vehicle", None)
        context.setdefault("show_add_modal", False)
        return context

    def post(self, request, *args, **kwargs):
        reg_number = request.POST.get("registration_number", "").strip().upper()
        duplicate_vehicle = (
            Vehicle.objects.filter(registration_number=reg_number).first() if reg_number else None
        )
        form = VehicleForm(request.POST)

        if duplicate_vehicle:
            messages.error(
                request,
                f"Vehicle {reg_number} is already registered. See the details below.",
            )
        elif form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.year = timezone.now().year
            vehicle.save()
            messages.success(request, f"Vehicle {vehicle.registration_number} registered successfully.")
            return redirect("fleet")

        context = self.get_context_data(**kwargs)
        context["vehicle_form"] = form
        context["duplicate_vehicle"] = duplicate_vehicle
        context["show_add_modal"] = True
        return self.render_to_response(context)


class DriversView(RoleSectionView):
    template_name = "users/drivers.html"
    rbac_module = "drivers"
    active_page = "drivers"
    page_title = "Drivers"
    page_subtitle = "Manage drivers, licenses, and current assignments."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.request.GET.get("status", "all")
        drivers = Driver.objects.select_related("assigned_vehicle").order_by("first_name", "last_name")
        if status != "all":
            drivers = drivers.filter(status=status)

        context["drivers"] = drivers
        context["status_filter"] = status
        context.setdefault("driver_form", DriverForm())
        context.setdefault("duplicate_driver", None)
        context.setdefault("show_add_modal", False)
        return context

    def post(self, request, *args, **kwargs):
        employee_id = request.POST.get("employee_id", "").strip().upper()
        license_number = request.POST.get("license_number", "").strip().upper()

        duplicate_driver = Driver.objects.filter(employee_id=employee_id).first() if employee_id else None
        if not duplicate_driver and license_number:
            duplicate_driver = Driver.objects.filter(license_number=license_number).first()

        form = DriverForm(request.POST)

        if duplicate_driver:
            messages.error(
                request,
                f"A driver with Employee ID {duplicate_driver.employee_id} or this License No. already exists. "
                "See the details below.",
            )
        elif form.is_valid():
            driver = form.save()
            messages.success(request, f"Driver {driver.first_name} {driver.last_name} added successfully.")
            return redirect("drivers")

        context = self.get_context_data(**kwargs)
        context["driver_form"] = form
        context["duplicate_driver"] = duplicate_driver
        context["show_add_modal"] = True
        return self.render_to_response(context)


class TripsView(RoleSectionView):
    template_name = "users/trips.html"
    rbac_module = "trips"
    active_page = "trips"
    page_title = "Trips"
    page_subtitle = "Track and manage fleet dispatch status."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.request.GET.get("status", "all")
        trips = Trip.objects.select_related("vehicle", "driver").order_by("-id")
        if status != "all":
            trips = trips.filter(status=status)

        context["trips"] = trips
        context["status_filter"] = status
        context.setdefault("trip_form", TripForm())
        context.setdefault("show_add_modal", False)
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "create")

        if action == "create":
            form = TripForm(request.POST)
            if form.is_valid():
                trip = form.save(commit=False)
                trip.status = "draft"
                trip.save()
                messages.success(
                    request,
                    f"Trip {trip.origin} → {trip.destination} created as a draft.",
                )
                return redirect("trips")
            context = self.get_context_data(**kwargs)
            context["trip_form"] = form
            context["show_add_modal"] = True
            return self.render_to_response(context)

        trip = Trip.objects.select_related("vehicle", "driver").filter(pk=request.POST.get("trip_id")).first()
        if not trip:
            messages.error(request, "Trip not found.")
            return redirect("trips")

        if action == "dispatch":
            if trip.status != "draft":
                messages.error(request, "Only draft trips can be dispatched.")
            elif trip.vehicle.status != "available":
                messages.error(request, f"Vehicle {trip.vehicle.registration_number} is not available.")
            elif trip.driver.status != "available":
                messages.error(request, f"Driver {trip.driver.first_name} {trip.driver.last_name} is not available.")
            else:
                trip.status = "dispatched"
                trip.start_time = timezone.now()
                trip.save()
                Vehicle.objects.filter(pk=trip.vehicle_id).update(status="on_trip")
                Driver.objects.filter(pk=trip.driver_id).update(status="on_trip")
                messages.success(request, f"Trip TR-{trip.id:04d} dispatched.")

        elif action == "complete":
            if trip.status != "dispatched":
                messages.error(request, "Only dispatched trips can be completed.")
            else:
                trip.status = "completed"
                trip.end_time = timezone.now()
                trip.save()
                Vehicle.objects.filter(pk=trip.vehicle_id).update(status="available")
                Driver.objects.filter(pk=trip.driver_id).update(status="available")
                messages.success(request, f"Trip TR-{trip.id:04d} completed.")

        elif action == "cancel":
            if trip.status not in ("draft", "dispatched"):
                messages.error(request, "Only draft or dispatched trips can be cancelled.")
            else:
                was_dispatched = trip.status == "dispatched"
                trip.status = "cancelled"
                trip.end_time = timezone.now()
                trip.save()
                if was_dispatched:
                    Vehicle.objects.filter(pk=trip.vehicle_id).update(status="available")
                    Driver.objects.filter(pk=trip.driver_id).update(status="available")
                messages.success(request, f"Trip TR-{trip.id:04d} cancelled.")

        return redirect("trips")


class MaintenanceView(RoleSectionView):
    template_name = "users/maintenance.html"
    allowed_roles = ("admin", "fleet_manager")
    active_page = "maintenance"
    page_title = "Maintenance"
    page_subtitle = "Manage repair schedules, work orders, and service history."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["logs"] = MaintenanceLog.objects.select_related("vehicle").order_by("-id")
        context.setdefault("maintenance_form", MaintenanceForm())
        context.setdefault("show_add_modal", False)
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get("action") == "resolve":
            log = MaintenanceLog.objects.select_related("vehicle").filter(pk=request.POST.get("log_id")).first()
            if log and not log.resolved:
                log.resolved = True
                log.save(update_fields=["resolved"])
                Vehicle.objects.filter(pk=log.vehicle_id).update(status="available")
                messages.success(
                    request,
                    f"{log.vehicle.registration_number} marked available after maintenance.",
                )
            return redirect("maintenance")

        form = MaintenanceForm(request.POST)
        if form.is_valid():
            log = form.save()
            messages.success(
                request,
                f"Maintenance logged for {log.vehicle.registration_number}; vehicle marked In Shop.",
            )
            return redirect("maintenance")

        context = self.get_context_data(**kwargs)
        context["maintenance_form"] = form
        context["show_add_modal"] = True
        return self.render_to_response(context)


def compute_fleet_utilization():
    active_vehicles = Vehicle.objects.exclude(status="retired").count()
    active_trips = Trip.objects.filter(status="dispatched").count()
    return round((active_trips / active_vehicles) * 100) if active_vehicles else 0


def compute_vehicle_metrics():
    rows = []
    for vehicle in Vehicle.objects.all().order_by("registration_number"):
        total_fuel_liters = vehicle.fuel_logs.aggregate(total=Sum("liters"))["total"] or Decimal("0")
        total_fuel_cost = vehicle.fuel_logs.aggregate(total=Sum("cost"))["total"] or Decimal("0")
        total_maintenance_cost = vehicle.maintenance_logs.aggregate(total=Sum("cost"))["total"] or Decimal("0")
        total_expense_cost = vehicle.expense_logs.aggregate(total=Sum("cost"))["total"] or Decimal("0")
        total_revenue = vehicle.revenue_logs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        total_distance = (
            vehicle.trips.filter(status="completed").aggregate(total=Sum("planned_distance_km"))["total"]
            or Decimal("0")
        )

        fuel_efficiency = (total_distance / total_fuel_liters) if total_fuel_liters else None
        operational_cost = total_fuel_cost + total_maintenance_cost
        roi = (total_revenue - operational_cost) / vehicle.acquisition_cost if vehicle.acquisition_cost else None
        roi_percent = roi * 100 if roi is not None else None

        rows.append(
            {
                "vehicle": vehicle,
                "total_fuel_liters": total_fuel_liters,
                "total_fuel_cost": total_fuel_cost,
                "total_maintenance_cost": total_maintenance_cost,
                "total_expense_cost": total_expense_cost,
                "total_distance": total_distance,
                "fuel_efficiency": fuel_efficiency,
                "operational_cost": operational_cost,
                "revenue": total_revenue,
                "roi": roi,
                "roi_percent": roi_percent,
            }
        )
    return rows


def compute_fleet_summary(vehicle_metrics):
    total_distance = sum((row["total_distance"] for row in vehicle_metrics), Decimal("0"))
    total_fuel_liters = sum((row["total_fuel_liters"] for row in vehicle_metrics), Decimal("0"))
    total_operational_cost = sum((row["operational_cost"] for row in vehicle_metrics), Decimal("0"))
    total_revenue = sum((row["revenue"] for row in vehicle_metrics), Decimal("0"))
    total_acquisition_cost = Vehicle.objects.aggregate(total=Sum("acquisition_cost"))["total"] or Decimal("0")

    fuel_efficiency = (total_distance / total_fuel_liters) if total_fuel_liters else None
    roi_percent = (
        (total_revenue - total_operational_cost) / total_acquisition_cost * 100
        if total_acquisition_cost
        else None
    )

    return {
        "fuel_efficiency": fuel_efficiency,
        "utilization": compute_fleet_utilization(),
        "operational_cost": total_operational_cost,
        "roi_percent": roi_percent,
    }


def compute_monthly_revenue(months=7):
    today = timezone.now().date()
    year, month = today.year, today.month
    month_keys = []
    for i in range(months - 1, -1, -1):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1
        month_keys.append((y, m))

    points = []
    for y, m in month_keys:
        total = (
            RevenueLog.objects.filter(date_logged__year=y, date_logged__month=m).aggregate(total=Sum("amount"))[
                "total"
            ]
            or Decimal("0")
        )
        points.append({"label": MONTH_ABBR[m], "amount": total})

    max_amount = max((p["amount"] for p in points), default=Decimal("0"))
    for p in points:
        p["percent"] = float(p["amount"] / max_amount * 100) if max_amount else 0
    return points


def compute_top_costliest_vehicles(vehicle_metrics, limit=3):
    ranked = sorted(vehicle_metrics, key=lambda row: row["operational_cost"], reverse=True)
    ranked = [row for row in ranked if row["operational_cost"] > 0][:limit]
    max_cost = max((row["operational_cost"] for row in ranked), default=Decimal("0"))
    palette = ["#f87171", "#f59e0b", "#3b82f6", "#a78bfa", "#34d399"]

    rows = []
    for i, row in enumerate(ranked):
        rows.append(
            {
                "vehicle": row["vehicle"],
                "operational_cost": row["operational_cost"],
                "percent": float(row["operational_cost"] / max_cost * 100) if max_cost else 0,
                "color": palette[i % len(palette)],
            }
        )
    return rows


class FuelView(RoleSectionView):
    template_name = "users/fuel.html"
    rbac_module = "fuel"
    active_page = "fuel"
    page_title = "Fuel & Expenses"
    page_subtitle = "Track fuel spend and operational expenses."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fuel_logs"] = FuelLog.objects.select_related("vehicle").order_by("-date_logged", "-id")
        context["expense_logs"] = ExpenseLog.objects.select_related("vehicle").order_by("-date_logged", "-id")
        context["vehicle_costs"] = [
            {
                "vehicle": row["vehicle"],
                "fuel_cost": row["total_fuel_cost"],
                "maintenance_cost": row["total_maintenance_cost"],
                "expense_cost": row["total_expense_cost"],
                "operational_cost": row["operational_cost"],
            }
            for row in compute_vehicle_metrics()
        ]
        context.setdefault("fuel_form", FuelLogForm())
        context.setdefault("expense_form", ExpenseLogForm())
        context.setdefault("show_fuel_modal", False)
        context.setdefault("show_expense_modal", False)
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get("action") == "log_expense":
            form = ExpenseLogForm(request.POST)
            if form.is_valid():
                log = form.save()
                messages.success(request, f"Expense logged for {log.vehicle.registration_number}.")
                return redirect("fuel")
            context = self.get_context_data(**kwargs)
            context["expense_form"] = form
            context["show_expense_modal"] = True
            return self.render_to_response(context)

        form = FuelLogForm(request.POST)
        if form.is_valid():
            log = form.save()
            messages.success(request, f"Fuel logged for {log.vehicle.registration_number}.")
            return redirect("fuel")
        context = self.get_context_data(**kwargs)
        context["fuel_form"] = form
        context["show_fuel_modal"] = True
        return self.render_to_response(context)


class AnalyticsView(RoleSectionView):
    template_name = "users/analytics.html"
    rbac_module = "analytics"
    active_page = "analytics"
    page_title = "Analytics"
    page_subtitle = "View utilization, cost, and fleet performance trends."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle_metrics = compute_vehicle_metrics()
        context["fleet_summary"] = compute_fleet_summary(vehicle_metrics)
        context["monthly_revenue"] = compute_monthly_revenue()
        context["top_costliest"] = compute_top_costliest_vehicles(vehicle_metrics)
        context["vehicle_metrics"] = vehicle_metrics
        context.setdefault("revenue_form", RevenueLogForm())
        context.setdefault("show_revenue_modal", False)
        return context

    def post(self, request, *args, **kwargs):
        form = RevenueLogForm(request.POST)
        if form.is_valid():
            log = form.save()
            messages.success(request, f"Revenue logged for {log.vehicle.registration_number}.")
            return redirect("analytics")

        context = self.get_context_data(**kwargs)
        context["revenue_form"] = form
        context["show_revenue_modal"] = True
        return self.render_to_response(context)


class AnalyticsCSVExportView(RoleSectionView):
    rbac_module = "analytics"

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="fleet_analytics.csv"'

        writer = csv.writer(response)
        writer.writerow(["Fleet Utilization (%)", compute_fleet_utilization()])
        writer.writerow([])
        writer.writerow(
            [
                "Registration No.",
                "Fuel Efficiency (km/l)",
                "Fuel Cost",
                "Maintenance Cost",
                "Operational Cost",
                "Revenue",
                "ROI",
            ]
        )
        for row in compute_vehicle_metrics():
            writer.writerow(
                [
                    row["vehicle"].registration_number,
                    f"{row['fuel_efficiency']:.2f}" if row["fuel_efficiency"] is not None else "N/A",
                    row["total_fuel_cost"],
                    row["total_maintenance_cost"],
                    row["operational_cost"],
                    row["revenue"],
                    f"{row['roi']:.2%}" if row["roi"] is not None else "N/A",
                ]
            )
        return response


class AnalyticsPDFExportView(RoleSectionView):
    rbac_module = "analytics"

    def get(self, request, *args, **kwargs):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, title="Fleet Analytics Report")
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("TransitOps Fleet Analytics Report", styles["Title"]),
            Paragraph(f"Fleet Utilization: {compute_fleet_utilization()}%", styles["Normal"]),
            Spacer(1, 12),
        ]

        data = [["Reg No.", "Fuel Eff. (km/l)", "Fuel Cost", "Maint. Cost", "Op. Cost", "Revenue", "ROI"]]
        for row in compute_vehicle_metrics():
            data.append(
                [
                    row["vehicle"].registration_number,
                    f"{row['fuel_efficiency']:.2f}" if row["fuel_efficiency"] is not None else "N/A",
                    str(row["total_fuel_cost"]),
                    str(row["total_maintenance_cost"]),
                    str(row["operational_cost"]),
                    str(row["revenue"]),
                    f"{row['roi']:.2%}" if row["roi"] is not None else "N/A",
                ]
            )

        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2a44")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7fb")]),
                ]
            )
        )
        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="fleet_analytics.pdf"'
        return response


class SettingsView(RoleSectionView):
    template_name = "users/settings.html"
    allowed_roles = ("admin",)
    active_page = "settings"
    page_title = "Settings"
    page_subtitle = "Configure system preferences and access controls."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("general_form", AppSettingsForm(instance=AppSettings.load()))
        context.setdefault("password_form", PasswordChangeForm(user=self.request.user))
        context["rbac_roles"] = RBAC_ROLES
        context["rbac_modules"] = RolePermission.MODULE_CHOICES
        context["access_choices"] = RolePermission.ACCESS_CHOICES
        access_map = {(rp.role, rp.module): rp.access for rp in RolePermission.objects.all()}
        context["rbac_grid"] = [
            {
                "role": role,
                "role_label": role_label,
                "cells": [
                    {"module": module, "access": access_map.get((role, module), "none")}
                    for module, _ in context["rbac_modules"]
                ],
            }
            for role, role_label in RBAC_ROLES
        ]
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "general":
            form = AppSettingsForm(request.POST, instance=AppSettings.load())
            if form.is_valid():
                form.save()
                messages.success(request, "General settings updated.")
                return redirect("settings")
            context = self.get_context_data(**kwargs)
            context["general_form"] = form
            return self.render_to_response(context)

        if action == "password":
            form = PasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password updated successfully.")
                return redirect("settings")
            context = self.get_context_data(**kwargs)
            context["password_form"] = form
            return self.render_to_response(context)

        if action == "rbac":
            for role, _ in RBAC_ROLES:
                for module in RBAC_MODULES:
                    value = request.POST.get(f"perm_{role}_{module}")
                    if value in ("full", "view", "none"):
                        RolePermission.objects.update_or_create(
                            role=role, module=module, defaults={"access": value}
                        )
            messages.success(request, "Role-based access updated.")
            return redirect("settings")

        return redirect("settings")
