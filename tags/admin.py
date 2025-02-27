from django.contrib import admin

from .models import Tag, TagResult


@admin.register(Tag)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('project', 'project_owner')


@admin.register(TagResult)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('tag',)
