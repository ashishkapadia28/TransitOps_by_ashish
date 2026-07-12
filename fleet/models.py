from django.db import models
from django.utils import timezone

class Vehicle(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('on_trip', 'On Trip'),
        ('in_shop', 'In Shop'),
        ('retired', 'Retired'),
    )
    VEHICLE_TYPE_CHOICES = (
        ('truck', 'Truck'),
        ('bus', 'Bus'),
        ('van', 'Van'),
        ('car', 'Car'),
        ('other', 'Other'),
    )
    REGION_CHOICES = (
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
        ('central', 'Central'),
    )
    registration_number = models.CharField(max_length=50, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='truck')
    region = models.CharField(max_length=20, choices=REGION_CHOICES, default='north')
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    odometer = models.PositiveIntegerField(default=0, help_text="Odometer reading in km")
    acquisition_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    cargo_capacity = models.IntegerField(help_text="Capacity in kg")

    def __str__(self):
        return f"{self.registration_number} - {self.make} {self.model}"

class Driver(models.Model):
    STATUS_CHOICES = (
        ('available', 'On Duty'),
        ('on_trip', 'On Trip'),
        ('inactive', 'Inactive'),
    )
    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    license_number = models.CharField(max_length=50, unique=True)
    license_expiry_date = models.DateField()
    assigned_vehicle = models.ForeignKey(
        Vehicle, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_drivers'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Trip(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('dispatched', 'Dispatched'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='trips')
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    cargo_weight = models.IntegerField(help_text="Weight in kg", default=0)
    planned_distance_km = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Planned distance in km")
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Trip {self.id} - {self.origin} to {self.destination}"

class FuelLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_logs')
    liters = models.DecimalField(max_digits=6, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    date_logged = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Fuel for {self.vehicle.registration_number} on {self.date_logged}"

class ExpenseLog(models.Model):
    CATEGORY_CHOICES = (
        ('toll', 'Toll'),
        ('other', 'Other'),
    )
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='expense_logs')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.CharField(max_length=200, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    date_logged = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.get_category_display()} for {self.vehicle.registration_number} on {self.date_logged}"

class RevenueLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='revenue_logs')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)
    date_logged = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Revenue for {self.vehicle.registration_number} on {self.date_logged}"

class MaintenanceLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_logs')
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    date_logged = models.DateField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            Vehicle.objects.filter(pk=self.vehicle_id).update(status='in_shop')

    def __str__(self):
        return f"Maintenance for {self.vehicle.registration_number} on {self.date_logged}"
