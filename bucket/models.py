import os

from django.core.validators import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from hashid_field.field import HashidAutoField
from django.conf import  settings

from bucket.managers import FolderManager, FileManager, LeftOverImageManager
from bucket.storage import CustomFileSystemStorage
from users.models import User
from utilities.functions import upload_files_to, upload_leftover_to
from utilities.validators import validate_filesystem_path
from model_utils import FieldTracker
from mptt.models import MPTTModel, TreeForeignKey


class Folder(TimeStampedModel, MPTTModel):
    id = HashidAutoField(prefix='folder_', primary_key=True)
    name = models.TextField(verbose_name=_("Name"), null=False, blank=False)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name=_("Resource Owner"),
                             related_name=_("folders"), null=False)
    budget = models.CharField(max_length=255, null=False, blank=False)
    path = models.TextField(unique=True, validators=[validate_filesystem_path], db_index=True)
    objects = FolderManager()
    tracker = FieldTracker(fields={'name', 'path'})

    def clean(self):
        if self.parent == self:
            raise ValidationError("A folder can't be its own parent")
        if self.parent:
            self.user = self.parent.user
            self.budget = self.parent.budget

        self.path = self.get_folder_path()

    def save(self, *args, **kwargs):
        self.clean()
        self.path = self.get_folder_path()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name + f" ({self.budget})"

    # noinspection PyUnresolvedReferences
    def get_folder_path(self) -> str:
        folder_path = ['mofreitas', 'clientes', self.user.email.__str__()]
        current_folder = self.parent
        while current_folder is not None:
            folder_path.insert(3, current_folder.name)
            current_folder = current_folder.parent
        folder_path.append(self.name)
        return "/".join(folder_path)

    class Meta:
        verbose_name: str = 'Folder'
        verbose_name_plural: str = 'Folders'
        ordering = ("-created",)
        constraints: list = [models.UniqueConstraint(fields=['name', 'parent', 'user', 'budget'], name="unique_Folder")]

    class MPTTMeta:
        order_insertion_by = ['name']


class File(TimeStampedModel):
    id = HashidAutoField(prefix='file_', primary_key=True)
    file_name = models.CharField(max_length=500)
    file_type = models.CharField(max_length=10)
    # file = ProtectedFileField(upload_to=upload_files_to)
    file = models.FileField(upload_to=upload_files_to, max_length=int(2e5), storage=CustomFileSystemStorage())
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name=_("files"))
    tracker = FieldTracker(fields={'file_name', 'file'})
    objects = FileManager()

    def __str__(self):
        return self.file_name

    # noinspection PyUnresolvedReferences,PyTypeChecker
    def get_file_path(self) -> str:
        return os.path.join(self.folder.path, f"{self.file_name}{self.file_type}")

    class Meta:
        verbose_name: str = 'File'
        verbose_name_plural: str = 'Files'
        ordering = ("-created",)
        constraints: list = [models.UniqueConstraint(fields=['file', 'folder'], name="unique_File")]


class LeftOverImage(TimeStampedModel):
    id = HashidAutoField(prefix='leftover_', primary_key=True)
    # file = ProtectedImageField(upload_to=upload_leftover_to)
    file = models.ImageField(upload_to=upload_leftover_to)
    corners = models.JSONField(verbose_name=_("Corners"))
    treated = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)
    x = models.FloatField(verbose_name="Bbox X")
    y = models.FloatField(verbose_name="Bbox Y")
    width = models.FloatField(verbose_name="Bbox width")
    height = models.FloatField(verbose_name="Bbox height")
    thickness = models.FloatField(verbose_name="Thickness", default=-1)
    ratio = models.FloatField(verbose_name="ratio pixels/mm")
    klass = models.CharField(max_length=50)
    batch = models.CharField(max_length=15, default="default")
    location_x = models.PositiveIntegerField(default=0, verbose_name="Shelf X position")
    location_y = models.PositiveIntegerField(default=0, verbose_name="Shelf Y position")

    objects = LeftOverImageManager()

    def __str__(self):
        return self.id.__str__()

