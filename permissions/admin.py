from django.contrib import admin

from .models import Permission, Group


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename')
    fields = ['name', 'codename']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    fields = ['name', 'permissions']
