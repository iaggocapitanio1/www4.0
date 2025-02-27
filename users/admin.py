from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CustomerProfile, WorkerProfile, OrganizationProfile
from django.contrib.sessions.models import Session


@admin.register(User)
class UserAdmin(UserAdmin):
    model = User
    fieldsets = auth_admin.UserAdmin.fieldsets + (
        ("Bio", {"fields": ("picture", "role",), }), ("Orion Permissions", {
            "fields": ("orion_groups", "user_orion_permissions",)
        }),)
    filter_horizontal = ('orion_groups',)
    list_display = ["username", "email", "role", "is_active"]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    @staticmethod
    def _session_data(obj):
        return obj.get_decoded()

    list_display = ['session_key', '_session_data', 'expire_date']


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vat')


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'hasOrganization', 'performanceRole')


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vat')
