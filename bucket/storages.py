from django.core.files.storage import FileSystemStorage
from django.conf import settings


class Storage(FileSystemStorage):
    """
       A class to manage protected files.
       We have to override the methods in the FileSystemStorage class which
       are decorated with cached_property for this class to work as intended.
       """

    def __init__(self, *args, **kwargs):
        kwargs["location"] = settings.PROTECTED_MEDIA_ROOT
        kwargs["base_url"] = settings.PROTECTED_MEDIA_URL
        super(Storage, self).__init__(*args, **kwargs)
