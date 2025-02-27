from django.dispatch import Signal

user_registered = Signal()

budget_changed = Signal()

save_budget = Signal()

budget_deleted = Signal()

project_deleted = Signal()

furniture_created = Signal()

furniture_deleted = Signal()

furniture_changed = Signal()