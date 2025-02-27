from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from .managers import PermissionManager, GroupManager
from hashid_field.field import HashidAutoField


class Permission(TimeStampedModel):
    id = HashidAutoField(prefix='permissions_', primary_key=True)
    name = models.CharField(_('name'), max_length=255)
    codename = models.CharField(_('codename'), max_length=100, unique=True)
    objects = PermissionManager()

    class Meta:
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        ordering = ['created']

    def __str__(self):
        return self.name


class Group(TimeStampedModel):
    id = HashidAutoField(prefix='group_', primary_key=True)
    name = models.CharField(max_length=150, unique=True)
    permissions = models.ManyToManyField(Permission, verbose_name=_('permissions'), blank=True)
    objects = GroupManager()

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')
        ordering = ['created']

    def __str__(self):
        return self.name
