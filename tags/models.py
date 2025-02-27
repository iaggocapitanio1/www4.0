from django.db import models
from django_extensions.db.models import TimeStampedModel
from hashid_field.field import HashidAutoField
from users.models import User
from utilities.functions import upload_pdf_to, upload_result_pdf_to
from tags.managers import TagManager, TagResultManager


class Tag(TimeStampedModel):
    id = HashidAutoField(prefix='tags_', primary_key=True)
    project = models.CharField(max_length=255, blank=False, null=False)
    project_owner = models.ForeignKey(User, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to=upload_pdf_to, null=False)
    excel = models.FileField(upload_to=upload_pdf_to, null=False)

    objects = TagManager()

    def __str__(self):
        return self.pdf.name.__str__()


class TagResult(TimeStampedModel):
    id = HashidAutoField(prefix='tag_result_', primary_key=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to=upload_result_pdf_to, null=False)
    objects = TagResultManager()

    def __str__(self):
        return self.pdf.name.__str__()
