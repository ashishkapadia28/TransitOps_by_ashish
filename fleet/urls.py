from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleViewSet, DriverViewSet, TripViewSet,
    FuelLogViewSet, ExpenseLogViewSet, RevenueLogViewSet, MaintenanceLogViewSet, DashboardStatsView
)

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet)
router.register(r'drivers', DriverViewSet)
router.register(r'trips', TripViewSet)
router.register(r'fuel', FuelLogViewSet)
router.register(r'expenses', ExpenseLogViewSet)
router.register(r'revenue', RevenueLogViewSet)
router.register(r'maintenance', MaintenanceLogViewSet)

urlpatterns = [
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
