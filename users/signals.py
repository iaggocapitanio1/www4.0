from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver

from emailManager.tasks import send_confirmation_email_and_reset_password_task
from permissions.models import Group as OrionGroup
from users.models import OrganizationProfile, WorkerProfile, CustomerProfile, User
from utilities.functions import map_owner_entities, batch_delete, create_user_folder
from utilities.payloads import customer_entity, worker_entity, organization_entity
from utilities.signals import user_registered


@receiver(user_registered)
def user_signup(sender, user, request, **kwargs):
    send_confirmation_email_and_reset_password_task(request=request, user=user)
    create_user_folder(user=user)


@receiver(pre_save, sender=User)
def verify_connection(sender, instance, **kwargs):
    from utilities.client import oauth
    import requests
    from django.conf import settings
    from utilities.exceptions import AuthenticationFiware
    if instance.is_superuser:
        return
    requests_header = settings.ORION_HEADERS.copy()
    if requests_header.get("Fiware-Service"):
        requests_header.pop("Fiware-Service")
    response = requests.get(settings.ORION_ENTITIES + "?type=Owner", auth=oauth, headers=requests_header)
    if response.status_code != 200:
        raise AuthenticationFiware(detail=response.text, code=response.status_code)


@receiver(post_save, sender=User)
def assign_user_to_group(sender, instance: User, created, **kwargs):
    try:
        if created:
            if instance.is_superuser:
                pass
            elif instance.role == User.Roles.CUSTOMER:
                group = Group.objects.get(name='Customers')
                orion_group: QuerySet = OrionGroup.objects.filter(name='Customers')
                instance.groups.add(group)
                if orion_group.exists():
                    instance.orion_groups.add(orion_group.first())
                instance.save()
            elif instance.role == User.Roles.WORKER:
                group = Group.objects.get(name='Workers')
                orion_group: QuerySet = OrionGroup.objects.filter(name='Workers')
                instance.groups.add(group)
                if orion_group.exists():
                    instance.orion_groups.add(orion_group.first())
                instance.save()
            elif instance.role == User.Roles.ADMIN:
                group = Group.objects.get(name='Organizations')
                orion_group: QuerySet = OrionGroup.objects.filter(name='Organizations')
                if orion_group.exists():
                    instance.orion_groups.add(orion_group.first())
                instance.groups.add(group)

                instance.save()
    except Exception as error:
        print(error)


@receiver(post_save, sender=OrganizationProfile)
def on_organization_save(sender, instance, created, **kwargs):
    organization = organization_entity(organization=instance)
    if created:
        organization.post()
    organization.patch()


@receiver(pre_delete, sender=OrganizationProfile)
def on_organization_delete(sender, instance, **kwargs):
    organization = organization_entity(organization=instance)
    organization.delete()


@receiver(post_delete, sender=OrganizationProfile)
def on_organization_post_delete(sender, instance, **kwargs):
    if instance.user:
        instance.user.delete()


@receiver(post_save, sender=WorkerProfile)
def on_work_save(sender, instance, created, **kwargs):
    worker = worker_entity(worker=instance)

    if created:
        worker.post()
    worker.patch()


@receiver(pre_delete, sender=WorkerProfile)
def on_work_delete(sender, instance, **kwargs):
    worker = worker_entity(worker=instance)
    worker.delete()


@receiver(post_delete, sender=WorkerProfile)
def on_worker_post_delete(sender, instance, **kwargs):
    if instance.user:
        instance.user.delete()


@receiver(post_save, sender=CustomerProfile)
def on_customer_save(sender, instance, created, **kwargs):
    customer = customer_entity(customer=instance)
    if created:
        customer.post()
    customer.patch()


@receiver(pre_delete, sender=CustomerProfile)
def on_customer_delete(sender, instance, **kwargs):
    customer = customer_entity(customer=instance)
    entities_related = map_owner_entities(owner_id=customer.id)
    batch_delete(entities_map=entities_related)
    customer.delete()


@receiver(post_delete, sender=CustomerProfile)
def on_customer_post_delete(sender, instance, **kwargs):
    if instance.user:
        instance.user.delete()
