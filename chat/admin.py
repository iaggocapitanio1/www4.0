from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'to', 'by', 'project', 'created']
    list_filter = ['to', 'by', 'project']
    search_fields = ['to__username', 'by__username', 'project', 'text']

