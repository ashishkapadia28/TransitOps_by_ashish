from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from fleet.models import Driver, ExpenseLog, FuelLog, MaintenanceLog, RevenueLog, Trip, Vehicle

VEHICLES = [
    dict(registration_number="MH-04-CD-5678", make="Tata", model="407", year=2022,
         vehicle_type="truck", region="west", status="available", cargo_capacity=1200, acquisition_cost=650000),
    dict(registration_number="GJ-01-EF-2345", make="Ashok Leyland", model="Dost", year=2021,
         vehicle_type="van", region="west", status="on_trip", cargo_capacity=1000, acquisition_cost=550000),
    dict(registration_number="KA-05-GH-8899", make="Mahindra", model="Bolero Pickup", year=2023,
         vehicle_type="truck", region="south", status="available", cargo_capacity=1500, acquisition_cost=720000),
    dict(registration_number="DL-08-IJ-1122", make="Force", model="Traveller", year=2020,
         vehicle_type="bus", region="north", status="in_shop", cargo_capacity=2500, acquisition_cost=950000),
    dict(registration_number="RJ-14-KL-3344", make="Maruti", model="Eeco", year=2022,
         vehicle_type="van", region="north", status="available", cargo_capacity=600, acquisition_cost=380000),
    dict(registration_number="TN-09-MN-5566", make="Tata", model="Ace Gold", year=2023,
         vehicle_type="truck", region="south", status="on_trip", cargo_capacity=900, acquisition_cost=480000),
    dict(registration_number="WB-02-OP-7788", make="Eicher", model="Pro 2049", year=2021,
         vehicle_type="truck", region="east", status="available", cargo_capacity=3000, acquisition_cost=1250000),
    dict(registration_number="UP-16-QR-9900", make="Bajaj", model="Maxima", year=2018,
         vehicle_type="van", region="central", status="retired", cargo_capacity=500, acquisition_cost=300000),
]

DRIVERS = [
    dict(employee_id="DR-101", first_name="Rohan", last_name="Mehta",
         license_number="MH-01-2019-11111", license_expiry_date="2027-08-01",
         vehicle_reg="MH-04-CD-5678", status="available"),
    dict(employee_id="DR-102", first_name="Sanjay", last_name="Kumar",
         license_number="GJ-01-2020-22222", license_expiry_date="2026-12-15",
         vehicle_reg="GJ-01-EF-2345", status="on_trip"),
    dict(employee_id="DR-103", first_name="Anita", last_name="Desai",
         license_number="KA-05-2018-33333", license_expiry_date="2027-11-30",
         vehicle_reg="KA-05-GH-8899", status="available"),
    dict(employee_id="DR-104", first_name="Vikram", last_name="Singh",
         license_number="DL-08-2021-44444", license_expiry_date="2028-01-20",
         vehicle_reg="DL-08-IJ-1122", status="inactive"),
    dict(employee_id="DR-105", first_name="Meera", last_name="Iyer",
         license_number="RJ-14-2019-55555", license_expiry_date="2027-03-10",
         vehicle_reg="RJ-14-KL-3344", status="available"),
    dict(employee_id="DR-106", first_name="Arjun", last_name="Nair",
         license_number="TN-09-2020-66666", license_expiry_date="2026-09-05",
         vehicle_reg="TN-09-MN-5566", status="on_trip"),
    dict(employee_id="DR-107", first_name="Divya", last_name="Reddy",
         license_number="WB-02-2022-77777", license_expiry_date="2029-06-18",
         vehicle_reg="WB-02-OP-7788", status="available"),
    dict(employee_id="DR-108", first_name="Karan", last_name="Malhotra",
         license_number="UP-16-2017-88888", license_expiry_date="2026-08-01",
         vehicle_reg=None, status="inactive"),
]

TRIPS = [
    dict(vehicle_reg="MH-04-CD-5678", employee_id="DR-101", origin="Mumbai", destination="Pune",
         cargo_weight=500, planned_distance_km=150, status="completed", days_ago_start=5, days_ago_end=4),
    dict(vehicle_reg="GJ-01-EF-2345", employee_id="DR-102", origin="Ahmedabad", destination="Surat",
         cargo_weight=700, planned_distance_km=260, status="dispatched", days_ago_start=1, days_ago_end=None),
    dict(vehicle_reg="KA-05-GH-8899", employee_id="DR-103", origin="Bengaluru", destination="Mysuru",
         cargo_weight=300, planned_distance_km=145, status="draft", days_ago_start=None, days_ago_end=None),
    dict(vehicle_reg="TN-09-MN-5566", employee_id="DR-106", origin="Chennai", destination="Coimbatore",
         cargo_weight=850, planned_distance_km=500, status="dispatched", days_ago_start=2, days_ago_end=None),
    dict(vehicle_reg="WB-02-OP-7788", employee_id="DR-107", origin="Kolkata", destination="Durgapur",
         cargo_weight=2000, planned_distance_km=170, status="completed", days_ago_start=10, days_ago_end=9),
    dict(vehicle_reg="RJ-14-KL-3344", employee_id="DR-105", origin="Jaipur", destination="Ajmer",
         cargo_weight=200, planned_distance_km=135, status="cancelled", days_ago_start=3, days_ago_end=3),
]

FUEL_LOG_VEHICLES = ["MH-04-CD-5678", "GJ-01-EF-2345", "KA-05-GH-8899", "TN-09-MN-5566", "WB-02-OP-7788", "RJ-14-KL-3344"]
REVENUE_LOG_VEHICLES = FUEL_LOG_VEHICLES
EXPENSE_LOG_VEHICLES = ["MH-04-CD-5678", "GJ-01-EF-2345", "TN-09-MN-5566"]


class Command(BaseCommand):
    help = "Seed realistic demo data for vehicles, drivers, trips, fuel, expenses, revenue, and maintenance."

    def handle(self, *args, **options):
        today = timezone.now().date()

        vehicles_by_reg = {}
        created_vehicles = 0
        for data in VEHICLES:
            vehicle, created = Vehicle.objects.get_or_create(
                registration_number=data["registration_number"], defaults=data
            )
            vehicles_by_reg[data["registration_number"]] = vehicle
            created_vehicles += created

        drivers_by_id = {}
        created_drivers = 0
        for data in DRIVERS:
            vehicle_reg = data.pop("vehicle_reg")
            defaults = dict(data)
            defaults.pop("employee_id")
            defaults["assigned_vehicle"] = vehicles_by_reg.get(vehicle_reg) if vehicle_reg else None
            driver, created = Driver.objects.get_or_create(employee_id=data["employee_id"], defaults=defaults)
            drivers_by_id[data["employee_id"]] = driver
            created_drivers += created
            data["vehicle_reg"] = vehicle_reg

        created_trips = 0
        for data in TRIPS:
            vehicle = vehicles_by_reg[data["vehicle_reg"]]
            driver = drivers_by_id[data["employee_id"]]
            if Trip.objects.filter(vehicle=vehicle, driver=driver, origin=data["origin"], destination=data["destination"]).exists():
                continue
            start_time = (
                timezone.now() - timedelta(days=data["days_ago_start"])
                if data["days_ago_start"] is not None
                else None
            )
            end_time = (
                timezone.now() - timedelta(days=data["days_ago_end"])
                if data["days_ago_end"] is not None
                else None
            )
            Trip.objects.create(
                vehicle=vehicle,
                driver=driver,
                origin=data["origin"],
                destination=data["destination"],
                cargo_weight=data["cargo_weight"],
                planned_distance_km=data["planned_distance_km"],
                status=data["status"],
                start_time=start_time,
                end_time=end_time,
            )
            created_trips += 1

        created_fuel = 0
        for reg in FUEL_LOG_VEHICLES:
            vehicle = vehicles_by_reg[reg]
            if vehicle.fuel_logs.exists():
                continue
            for months_ago, liters, cost in [(3, 42, 3600), (2, 48, 4150), (1, 45, 3950), (0, 50, 4400)]:
                FuelLog.objects.create(
                    vehicle=vehicle,
                    liters=liters,
                    cost=cost,
                    date_logged=today - timedelta(days=months_ago * 30),
                )
                created_fuel += 1

        created_revenue = 0
        base_amounts = [18000, 21000, 19500, 24000, 26500, 25000, 29000]
        for i, reg in enumerate(REVENUE_LOG_VEHICLES):
            vehicle = vehicles_by_reg[reg]
            if vehicle.revenue_logs.exists():
                continue
            for months_ago in range(7):
                amount = base_amounts[6 - months_ago]
                RevenueLog.objects.create(
                    vehicle=vehicle,
                    amount=amount + (i * 1500),
                    description="Freight delivery revenue",
                    date_logged=today - timedelta(days=months_ago * 30),
                )
                created_revenue += 1

        created_expense = 0
        for reg in EXPENSE_LOG_VEHICLES:
            vehicle = vehicles_by_reg[reg]
            if vehicle.expense_logs.exists():
                continue
            for months_ago, category, cost, description in [
                (2, "toll", 380, "Expressway toll"),
                (1, "other", 220, "Parking & permit fees"),
            ]:
                ExpenseLog.objects.create(
                    vehicle=vehicle,
                    category=category,
                    description=description,
                    cost=cost,
                    date_logged=today - timedelta(days=months_ago * 30),
                )
                created_expense += 1

        created_maintenance = 0
        in_shop_vehicle = vehicles_by_reg["DL-08-IJ-1122"]
        if not in_shop_vehicle.maintenance_logs.exists():
            MaintenanceLog.objects.create(
                vehicle=in_shop_vehicle,
                description="Engine overheating - diagnostics and coolant system repair",
                cost=8500,
            )
            created_maintenance += 1

        historical_vehicle = vehicles_by_reg["TN-09-MN-5566"]
        if not historical_vehicle.maintenance_logs.exists():
            log = MaintenanceLog.objects.create(
                vehicle=historical_vehicle,
                description="Routine brake pad replacement",
                cost=3200,
            )
            log.resolved = True
            log.save(update_fields=["resolved"])
            Vehicle.objects.filter(pk=historical_vehicle.pk).update(status="on_trip")
            created_maintenance += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded: {created_vehicles} vehicles, {created_drivers} drivers, {created_trips} trips, "
            f"{created_fuel} fuel logs, {created_revenue} revenue logs, {created_expense} expense logs, "
            f"{created_maintenance} maintenance logs (existing records were left untouched)."
        ))
