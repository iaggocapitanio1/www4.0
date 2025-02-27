from django.contrib import admin
from bucket.models import File, Folder, LeftOverImage
from mptt.admin import MPTTModelAdmin


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'folder', 'folder_budget')
    list_filter = ('folder__budget',)

    def folder_budget(self, obj):
        return obj.folder.budget

    folder_budget.short_description = 'Budget'


@admin.register(Folder)
class FolderAdmin(MPTTModelAdmin):
    list_display = ('name', 'user', 'budget', 'path')
    list_filter = ('user', 'budget')
    search_fields = ('folder_name', 'user__email')

    class MPTTMeta:
        order_insertion_by = ['name']


@admin.register(LeftOverImage)
class LeftOverImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'treated', 'confirmed', 'klass', 'batch')
    list_filter = ('treated', 'confirmed', 'klass', 'batch')
    search_fields = ('klass', 'batch')
