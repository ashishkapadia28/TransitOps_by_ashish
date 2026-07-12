from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AppSettings, CustomUser, RolePermission

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'username', 'role', 'is_staff']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['email']
    fieldsets = UserAdmin.fieldsets + (
        ('TransitOps', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('TransitOps', {'fields': ('email', 'role')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ('depot_name', 'currency', 'distance_unit')


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'module', 'access')
    list_filter = ('role', 'module', 'access')
