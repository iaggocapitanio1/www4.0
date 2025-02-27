import os

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from tags.models import Tag, TagResult
from tags.tasks import process_task


@receiver(post_save, sender=Tag)
def on_save_tag(sender, instance: Tag, created, **kwargs):
    process_task.delay(instance.pdf.path, instance.excel.path, instance.id.__str__(), created, None)


@receiver(post_delete, sender=Tag)
def delete_files(sender, instance, **kwargs):
    try:
        if os.path.exists(instance.pdf.path):
            instance.pdf.delete(save=False)
    except ValueError:
        pass

    try:
        if os.path.exists(instance.excel.path):
            instance.excel.delete(save=False)
    except ValueError:
        pass


@receiver(post_delete, sender=TagResult)
def delete_files(sender, instance, **kwargs):
    try:
        if os.path.exists(instance.pdf.path):
            instance.pdf.delete(save=False)
    except ValueError:
        pass
