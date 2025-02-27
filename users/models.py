from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from hashid_field.field import HashidAutoField
from vies.models import VATINField
from .managers import CustomerManager, UserManager, OrganizationManager, WorkManager
from utilities.managers import AddressManager
from permissions.models import Group, Permission
from typing import Union
from utilities.functions import upload_avatar_to


class Address(TimeStampedModel):
    id = HashidAutoField(prefix='address_', primary_key=True)
    streetAddress = models.CharField(max_length=50, blank=True, verbose_name=_("Street Address"))
    postalCode = models.CharField(max_length=15, blank=True, verbose_name=_("Postal Code"))
    addressLocality = models.CharField(max_length=25, blank=True, verbose_name=_("Address Locality"))
    addressRegion = models.CharField(max_length=25, blank=True, verbose_name=_("Address Region"))
    addressCountry = models.CharField(max_length=2, blank=True, verbose_name=_("Address Country"))
    objects = AddressManager()

    class Meta:
        verbose_name: str = 'Address'
        verbose_name_plural: str = 'Addresses'
        ordering = ("-created",)


class User(AbstractUser):
    class Roles(models.IntegerChoices):
        ADMIN = 0, _("Administrator")
        WORKER = 1, _("Worker")
        CUSTOMER = 2, _("Customer")

        def __str__(self):
            return self.name

    class Meta:
        verbose_name: str = 'User'
        verbose_name_plural: str = 'Users'
        permissions = [
            ('can_active', 'can_active'),
        ]

    id = HashidAutoField(prefix='user_', primary_key=True)
    picture = models.ImageField(blank=True, null=True, verbose_name=_("profile picture"), upload_to=upload_avatar_to)
    role = models.PositiveSmallIntegerField(choices=Roles.choices, default=Roles.CUSTOMER, verbose_name=_("Role"))
    email = models.EmailField(_('email address'), unique=True)
    objects = UserManager()
    orion_groups = models.ManyToManyField(
        Group,
        verbose_name=_('orion groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="user_set",
        related_query_name="user",
    )
    user_orion_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('orion user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="user_set",
        related_query_name="user",
    )

    @property
    def is_admin(self) -> bool:
        return self.role == self.Roles.ADMIN

    @property
    def is_worker(self) -> bool:
        return self.role == self.Roles.WORKER

    @property
    def is_customer(self) -> bool:
        return self.role == self.Roles.CUSTOMER

    def get_orion_group_permissions(self) -> models.QuerySet:
        groups = self.orion_groups.all()
        permissions = Permission.objects.filter(group__in=groups)
        return permissions.order_by()

    def get_orion_permissions(self) -> models.QuerySet:
        return self.user_orion_permissions.all().order_by()

    def get_orion_groups(self) -> models.QuerySet:
        return self.orion_groups.all().order_by()

    def delete_orion_permissions(self):
        return self.user_orion_permissions.clear()

    def delete_orion_groups(self):
        return self.orion_groups.clear()

    def get_all_orion_permissions(self) -> models.QuerySet:
        return self.get_orion_group_permissions().union(self.get_orion_permissions(), all=True)

    def has_orion_perm(self, perm: Union[Permission, str]):
        if isinstance(perm, str):
            try:
                perm = Permission.objects.get(codename=perm)
            except Exception:
                return False
        return perm in self.get_all_orion_permissions()

    def __str__(self) -> str:
        return self.username


class OrganizationProfile(TimeStampedModel):
    id = HashidAutoField(prefix='organization_', primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"), related_name='organization')
    vat = VATINField(unique=True, blank=True, null=True, verbose_name=_("VAT"))
    objects = OrganizationManager()

    class Meta:
        verbose_name: str = 'Organization'
        verbose_name_plural: str = 'Organizations'
        ordering = ("-created",)

    def __str__(self) -> str:
        return self.user.__str__()


class WorkerProfile(TimeStampedModel):
    class Station(models.IntegerChoices):
        CNC = 0, _("CNC operator")
        NESTING = 1, _("Nesting operator")
        MANUAL_CUTTING = 2, _("Manual cutting operator")
        ASSEMBLY = 3, _("Assembly operator")
        MANAGER = 4, _("Manager")
        OFFICE = 5, _("Officer operator")
        WAREHOUSE = 6, _("Warehouse operator")
        OTHER = 7, _("Other")

    class Meta:
        verbose_name: str = 'Worker'
        verbose_name_plural: str = 'Worker'
        ordering = ("-created",)

    objects = WorkManager()
    id = HashidAutoField(prefix='worker_', primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"), related_name='worker')
    hasOrganization = models.ForeignKey(OrganizationProfile, on_delete=models.CASCADE, related_name='workers')
    performanceRole = models.PositiveSmallIntegerField(choices=Station.choices, verbose_name=_("Performance Role"))

    def __str__(self) -> str:
        return self.user.__str__()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('users:worker-detail', kwargs={'pk': self.pk})


class CustomerProfile(TimeStampedModel):
    id = HashidAutoField(prefix='customer_', primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"), related_name='customer')
    address = models.ForeignKey(to=Address,
                                on_delete=models.CASCADE,
                                related_name='customers',
                                null=True)
    delivery_address = models.ForeignKey(to=Address,
                                         on_delete=models.CASCADE,
                                         related_name='delivery_addresses',
                                         null=True)
    vat = VATINField(unique=True, blank=True, null=True)
    tos = models.BooleanField(_("Terms of Service"), default=False)
    isCompany = models.BooleanField(_("is a Institution?"), default=False)
    objects = CustomerManager()

    class Meta:
        verbose_name: str = 'Customer'
        verbose_name_plural: str = 'Customer'
        ordering = ("-created",)

    def __str__(self):
        return self.user.__str__()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('users:customer-detail', kwargs={'pk': self.pk})
