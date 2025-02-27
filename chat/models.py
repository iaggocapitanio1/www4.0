from django.db import models
from hashid_field.field import HashidAutoField
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
User = get_user_model()


class MessageManager(models.Manager):
    pass


class Message(TimeStampedModel):
    id = HashidAutoField(prefix='message_', primary_key=True)
    to = models.ForeignKey(to=User, verbose_name=_("Sent To"), on_delete=models.CASCADE, related_name="to_user")
    by = models.ForeignKey(to=User, verbose_name=_("Sent By"), on_delete=models.CASCADE, related_name="by_user")
    project = models.CharField(max_length=255, default='', verbose_name=_("Project"))
    text = models.CharField(max_length=255, blank=True)
    objects = MessageManager()

    def __str__(self):
        return self.project.__str__()

    class Meta:
        verbose_name: str = 'Message'
        verbose_name_plural: str = 'Messages'
        ordering = ("-created",)