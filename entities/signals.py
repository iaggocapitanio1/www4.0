from django.dispatch import receiver

from emailManager.tasks import send_budget_changed_task
from utilities.functions import create_budget_folder, map_project_entities, batch_delete
from utilities.signals import budget_changed, save_budget, project_deleted


@receiver(project_deleted)
def on_project_deleted(sender, pk, **kwargs):
    entities_map = map_project_entities(project_id=pk)
    batch_delete(entities_map)


@receiver(budget_changed)
def budget_changed(sender, data, budget, **kwargs):
    send_budget_changed_task.delay(data=data, budget=budget)


@receiver(save_budget)
def on_save_budget(sender, budget_id, **kwargs):
    create_budget_folder(budget_id=budget_id)
