from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from .models import Vehicle, Driver, Trip, FuelLog, ExpenseLog, RevenueLog, MaintenanceLog
from .serializers import (
    VehicleSerializer, DriverSerializer, TripSerializer,
    FuelLogSerializer, ExpenseLogSerializer, RevenueLogSerializer, MaintenanceLogSerializer
)
from users.permissions import HasRole

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, HasRole]
    allowed_roles = ["admin", "fleet_manager"]

class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [IsAuthenticated, HasRole]
    allowed_roles = ["admin", "fleet_manager"]

class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated, HasRole]
    allowed_roles = ["admin", "fleet_manager", "dispatcher"]

    @action(detail=True, methods=['post'])
    def dispatch_trip(self, request, pk=None):
        with transaction.atomic():
            trip = self.get_object()
            if trip.status != 'draft':
                return Response({'error': 'Only draft trips can be dispatched'}, status=status.HTTP_400_BAD_REQUEST)

            vehicle = trip.vehicle
            driver = trip.driver

            if vehicle.status != 'available':
                return Response({'error': 'Vehicle is not available'}, status=status.HTTP_400_BAD_REQUEST)
            if driver.status != 'available':
                return Response({'error': 'Driver is not available'}, status=status.HTTP_400_BAD_REQUEST)

            # Update statuses together so the assignment stays consistent.
            trip.status = 'dispatched'
            trip.start_time = timezone.now()
            trip.save()

            vehicle.status = 'on_trip'
            vehicle.save()

            driver.status = 'on_trip'
            driver.save()

        return Response({'status': 'trip dispatched'})

    @action(detail=True, methods=['post'])
    def complete_trip(self, request, pk=None):
        trip = self.get_object()
        if trip.status != 'dispatched':
            return Response({'error': 'Only dispatched trips can be completed'}, status=status.HTTP_400_BAD_REQUEST)
        
        trip.status = 'completed'
        trip.end_time = timezone.now()
        trip.save()

        vehicle = trip.vehicle
        vehicle.status = 'available'
        vehicle.save()

        driver = trip.driver
        driver.status = 'available'
        driver.save()

        return Response({'status': 'trip completed'})

class FuelLogViewSet(viewsets.ModelViewSet):
    queryset = FuelLog.objects.all()
    serializer_class = FuelLogSerializer
    permission_classes = [IsAuthenticated, HasRole]
    allowed_roles = ["admin", "fleet_manager", "financial_analyst"]

class ExpenseLogViewSet(viewsets.ModelViewSet):
    queryset = ExpenseLog.objects.all()
    serializer_class = ExpenseLogSerializer
    permission_classes = [IsAuthenticated, HasRole]
    allowed_roles = ["admin", "fleet_manager", "financial_analyst"]

class RevenueLogViewSet(viewsets.ModelViewSet):
    queryset = RevenueLog.objects.all()
    serializer_class = RevenueLogSerializer
    permission_classes = [IsAuthenticated, HasRole]
    allowed_roles = ["admin", "fleet_manager", "financial_analyst"]

class MaintenanceLogViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceLog.objects.all()
    serializer_class = MaintenanceLogSerializer
    permission_classes = [IsAuthenticated, HasRole]
    allowed_roles = ["admin", "fleet_manager"]

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, HasRole]
    allowed_roles = ["admin", "fleet_manager", "financial_analyst"]

    def get(self, request):
        total_vehicles = Vehicle.objects.count()
        active_vehicles = Vehicle.objects.exclude(status='retired').count()
        on_trip_vehicles = Vehicle.objects.filter(status='on_trip').count()
        
        total_drivers = Driver.objects.count()
        available_drivers = Driver.objects.filter(status='available').count()
        
        active_trips = Trip.objects.filter(status='dispatched').count()
        
        total_fuel_cost = FuelLog.objects.aggregate(total=Sum('cost'))['total'] or 0
        total_maintenance_cost = MaintenanceLog.objects.aggregate(total=Sum('cost'))['total'] or 0

        return Response({
            'total_vehicles': total_vehicles,
            'active_vehicles': active_vehicles,
            'on_trip_vehicles': on_trip_vehicles,
            'total_drivers': total_drivers,
            'available_drivers': available_drivers,
            'active_trips': active_trips,
            'total_fuel_cost': total_fuel_cost,
            'total_maintenance_cost': total_maintenance_cost,
        })
