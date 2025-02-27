from django.db import models


class FolderManager(models.Manager):

    def __create_folder(self, name: str, parent: str):
        return self.model(name=name, parent=parent)

    def create_folder(self, name: str, parent: str):
        return self.__create_folder(name=name, parent=parent)


class FileManager(models.Manager):

    def __create_file(self, user, file_name: str, file_type: str, **kwargs):
        return self.model(user=user, file_name=file_name, file_type=file_type, **kwargs)

    def create_file(self, user, file_name: str, file_type: str, **kwargs):
        return self.__create_file(user=user, file_name=file_name, file_type=file_type, **kwargs)


class LeftOverImageManager(models.Manager):
    pass


class EASMManager(models.Manager):
    pass


class FurnitureCutListManager(models.Manager):
    pass


