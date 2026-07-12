from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be set.")

        email = self.normalize_email(email)
        username = extra_fields.get("username") or email.split("@")[0]
        extra_fields.setdefault("username", username)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('fleet_manager', 'Fleet Manager'),
        ('dispatcher', 'Dispatcher'),
        ('safety_officer', 'Safety Officer'),
        ('financial_analyst', 'Financial Analyst'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='dispatcher')

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.email} ({self.role})"


class AppSettings(models.Model):
    depot_name = models.CharField(max_length=100, default="Main Depot")
    currency = models.CharField(max_length=20, default="INR (₹)")
    distance_unit = models.CharField(max_length=20, default="Kilometers")

    def __str__(self):
        return self.depot_name

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class RolePermission(models.Model):
    MODULE_CHOICES = (
        ('fleet', 'Fleet'),
        ('drivers', 'Drivers'),
        ('trips', 'Trips'),
        ('fuel', 'Fuel & Expenses'),
        ('analytics', 'Analytics'),
    )
    ACCESS_CHOICES = (
        ('full', 'Full'),
        ('view', 'View'),
        ('none', 'No Access'),
    )
    role = models.CharField(max_length=20, choices=CustomUser.ROLE_CHOICES)
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    access = models.CharField(max_length=10, choices=ACCESS_CHOICES, default='none')

    class Meta:
        unique_together = ("role", "module")

    def __str__(self):
        return f"{self.role} / {self.module}: {self.access}"
