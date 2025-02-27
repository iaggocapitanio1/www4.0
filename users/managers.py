from django.contrib.auth.models import BaseUserManager
from django.contrib.auth import models as auth_models
from django.db import models


class UserManager(auth_models.UserManager, BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)
        extra_fields.setdefault("role", self.model.Roles.CUSTOMER)
        if username is None:
            username = email
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault("role", self.model.Roles.ADMIN)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)


class OrganizationManager(models.Manager):
    def create_organization(self, user, vat, **kwargs):
        return self.create(user=user, vat=vat, **kwargs)


class CustomerManager(models.Manager):
    def create_customer(self, user, vat, tos, isCompany, **kwargs):
        return self.create(user=user, vat=vat, tos=tos, isCompany=isCompany, **kwargs)


class WorkManager(models.Manager):
    def create_worker(self, user, hasOrganization, **kwargs):
        return self.create(user=user, hasOrganization=hasOrganization, **kwargs)
