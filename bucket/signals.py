import logging
import os
import shutil
from pathlib import Path

import signal_disabler
from django.conf import settings
from django.db.models.signals import pre_delete, post_save, pre_save
from django.dispatch import receiver

from bucket.models import File, Folder, LeftOverImage
from utilities.functions import get_folder_path, create_path, create_folders_for_furniture, \
    delete_folders_for_furniture, delete_budget_folder, map_budget_entities, batch_delete, update_folder_for_furniture \
    , update_folder_file_system
from utilities.signals import furniture_created, furniture_deleted, budget_deleted, furniture_changed
from utilities.payloads import leftover_entity

logger = logging.getLogger(__name__)


@receiver(furniture_changed)
def on_furniture_changed(sender, pk, old_name, **kwargs):
    update_folder_for_furniture(furniture_id=pk, old_name=old_name)


@receiver(pre_delete, sender=File)
def on_file_delete(sender, instance, **kwargs):
    path = Path(instance.file.path)
    if instance.file and path.exists() and path.is_file():
        os.remove(path.__str__())


@receiver(pre_delete, sender=Folder)
def on_folder_delete(sender, instance, **kwargs):
    folder_path: Path = settings.MEDIA_ROOT.joinpath(instance.get_folder_path())
    if folder_path.exists():
        shutil.rmtree(folder_path)


@receiver(furniture_created)
def on_furniture_post_created(sender, pks, **kwargs):
    for pk in pks:
        create_folders_for_furniture(furniture_id=pk)


@receiver(furniture_deleted)
def on_furniture_post_delete(sender, pk, **kwargs):
    delete_folders_for_furniture(furniture_id=pk)


@receiver(budget_deleted)
def on_budget_post_delete(sender, pk, **kwargs):
    delete_budget_folder(budget_id=pk)
    entities_map = map_budget_entities(budget_id=pk)
    batch_delete(entities_map=entities_map)


@receiver(post_save, sender=Folder)
def on_folder_post_save(sender: Folder, instance: Folder, created, **kwargs):
    if created:
        path = get_folder_path(instance)
        instance.path = path
        create_path(target=path)
        instance.save()


@signal_disabler.disable()
@receiver(post_save, sender=Folder)
def update_file_paths(sender, instance, created, **kwargs):
    if not created:
        for descendant in instance.get_descendants(include_self=True):
            for file in descendant.files.all():
                file.file.name = file.get_file_path()
                file.save()


@receiver(pre_save, sender=Folder)
def on_folder_pre_save(sender: Folder, instance: Folder, **kwargs):
    if instance.tracker.has_changed('path') and instance.tracker.previous('path') is not None:
        old_path = instance.tracker.previous('path')
        new_path = instance.path
        new_parent = instance.parent
        if update_folder_file_system(old_path, new_path, new_parent=new_parent):
            logger.info(f"Successfully updated the folder from '{old_path}' to '{instance.path}'.")
        else:
            logger.error(f"No folder found at '{old_path}' in the filesystem.")
            create_path(target=old_path)
            if update_folder_file_system(old_path, new_path, new_parent=new_parent):
                logger.info(f"Successfully created the folder from '{old_path}' to '{instance.path}'.")
            else:
                logger.error(f"An error occurred while attempting to update the folder. No corresponding folder was "
                             f"found in the filesystem at the following location: '{old_path}'.")


@receiver(post_save, sender=LeftOverImage)
def on_post_save_leftover(sender: Folder, instance: LeftOverImage, created, **kwargs):
    if instance.confirmed:
        leftover = leftover_entity(leftover=instance)
        response = leftover.get()
        if response.status_code != 200:
            leftover.post()
        else:
            leftover.patch()


@receiver(pre_delete, sender=LeftOverImage)
def on_work_delete(sender, instance, **kwargs):
    leftover = leftover_entity(leftover=instance)
    leftover.delete()
