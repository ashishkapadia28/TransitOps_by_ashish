from django.urls import path

from .api_views import MeAPIView, RegisterAPIView
from .views import (
    AnalyticsCSVExportView,
    AnalyticsPDFExportView,
    AnalyticsView,
    AuthLandingView,
    DashboardView,
    DriversView,
    FleetView,
    FuelView,
    LoginPageView,
    LogoutPageView,
    MaintenanceView,
    SettingsView,
    SignupPageView,
    TripsView,
)

urlpatterns = [
    path("", AuthLandingView.as_view(), name="home"),
    path("login/", LoginPageView.as_view(), name="login"),
    path("signup/", SignupPageView.as_view(), name="signup"),
    path("logout/", LogoutPageView.as_view(), name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("fleet/", FleetView.as_view(), name="fleet"),
    path("drivers/", DriversView.as_view(), name="drivers"),
    path("trips/", TripsView.as_view(), name="trips"),
    path("maintenance/", MaintenanceView.as_view(), name="maintenance"),
    path("fuel/", FuelView.as_view(), name="fuel"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("analytics/export/csv/", AnalyticsCSVExportView.as_view(), name="analytics-export-csv"),
    path("analytics/export/pdf/", AnalyticsPDFExportView.as_view(), name="analytics-export-pdf"),
    path("settings/", SettingsView.as_view(), name="settings"),
    path("api/auth/register/", RegisterAPIView.as_view(), name="api-register"),
    path("api/auth/me/", MeAPIView.as_view(), name="api-me"),
]
