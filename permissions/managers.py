from django.db import models


class GroupManager(models.Manager):
    """
    The manager for the auth's Group model.
    """
    use_in_migrations = True

    def get_by_natural_key(self, name):
        return self.get(name=name)


class PermissionManager(models.Manager):
    use_in_migrations = True

    def get_by_natural_key(self, codename, app_label, model):
        return self.get(codename=codename)
