from django.contrib import admin

from .models import Vehicle, Driver, Trip, FuelLog, ExpenseLog, RevenueLog, MaintenanceLog


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "vehicle_type", "region", "make", "model", "year", "status", "cargo_capacity", "acquisition_cost")
    search_fields = ("registration_number", "make", "model", "vehicle_type", "region")
    list_filter = ("vehicle_type", "status", "region", "make", "year")


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "first_name", "last_name", "license_number", "status", "license_expiry_date", "assigned_vehicle")
    search_fields = ("employee_id", "first_name", "last_name", "license_number")
    list_filter = ("status",)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("id", "vehicle", "driver", "origin", "destination", "status", "start_time", "end_time")
    list_filter = ("status",)
    search_fields = ("origin", "destination", "vehicle__registration_number", "driver__first_name", "driver__last_name")


@admin.register(FuelLog)
class FuelLogAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "liters", "cost", "date_logged")
    list_filter = ("date_logged",)


@admin.register(ExpenseLog)
class ExpenseLogAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "category", "cost", "date_logged")
    list_filter = ("category", "date_logged")


@admin.register(RevenueLog)
class RevenueLogAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "amount", "date_logged")
    list_filter = ("date_logged",)


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "cost", "date_logged", "resolved")
    list_filter = ("date_logged", "resolved")
