import os
import re
from pathlib import Path

from django.conf import settings
from django.core.files import File as DjangoFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.query import QuerySet
from hashid_field.rest import HashidSerializerCharField
from rest_framework import serializers
from rest_framework.reverse import reverse

from bucket.models import File, Folder, LeftOverImage
from users.models import User
from utilities.fields import PrimaryKeyRelatedFieldHashed
from utilities.functions import is_valid_sys_path
from utilities.geo import create_polygon


class FolderSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    files = PrimaryKeyRelatedFieldHashed(library="bucket", model=File, many=True, read_only=True)
    parent = PrimaryKeyRelatedFieldHashed(library="bucket", model=Folder, required=False, allow_null=True)
    user = PrimaryKeyRelatedFieldHashed(library="users", model=User)
    url = serializers.SerializerMethodField()

    def get_url(self, obj) -> str:
        return self.context.get('request').build_absolute_uri(reverse("storages:folder-detail", kwargs=dict(pk=obj.pk)))

    def get_action(self) -> str:
        return self.context.get('view').action

    @staticmethod
    def clean_name(value):
        if not is_valid_sys_path(value):
            raise serializers.ValidationError("The folder name is not valid!")
        return value

    def validate(self, attrs):
        parent = attrs.get('parent')
        name = attrs.get('name', self.instance.name if self.instance else None)

        if parent:
            attrs.update({'user': parent.user, 'budget': parent.budget})

        if self.instance is not None and parent == self.instance:
            raise serializers.ValidationError("A folder can't be its own parent")
        if not name:
            return attrs

        parent = parent or (self.instance.parent if self.instance else None)

        if not parent:
            return attrs

        # Add validation to prevent a parent folder from being updated to a child folder
        if self.instance and self.instance.pk:
            if self.instance.get_descendants().filter(pk=parent.pk).exists():
                raise serializers.ValidationError({'parent': 'A parent folder cannot be updated to a child folder.'})

        qs: QuerySet = Folder.objects.filter(parent=parent, name=name)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError({
                'name': "A folder with the same name already exists in the parent folder"
            })

        return attrs

    class Meta(object):
        model = Folder
        fields = ('id', 'name', 'files', 'path', "budget", "parent", 'user', 'modified', 'created', "url")
        extra_kwargs = {
            'id': {'read_only': True},
            'path': {'read_only': True}
        }


class FolderCreateByEmailSerializer(FolderSerializer):
    email = serializers.EmailField(write_only=True)

    def create(self, validated_data):
        email = validated_data.pop('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "User with this email does not exist"})

        validated_data['user'] = user
        return super().create(validated_data)

    class Meta(FolderSerializer.Meta):
        fields = ('id', 'name', 'files', 'path', "budget", "parent", 'email', 'modified', 'created', "url")
        extra_kwargs = {
            'id': {'read_only': True},
            'path': {'read_only': True}
        }


class FileSerializers(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    folder = PrimaryKeyRelatedFieldHashed(library="bucket", model=Folder)
    url = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()

    @staticmethod
    def get_path(obj):
        return obj.get_file_path()

    @staticmethod
    def validate_budget(value):
        if not re.match(r'^[a-zA-Z0-9_: -]+$', value):
            raise serializers.ValidationError("Invalid folder name")
        return value

    def get_url(self, obj) -> str:
        return self.context.get('request').build_absolute_uri(reverse("storages:file-detail", kwargs=dict(pk=obj.pk)))

    def validate(self, attrs):
        file = attrs.get('file')
        folder = attrs.get('folder')
        file_name, file_type = os.path.splitext(file.name)
        attrs.update(dict(file_name=file_name, file_type=file_type))
        qs: QuerySet = File.objects.filter(folder=folder, file_name=file_name, file_type=file_type)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A file with the same name already exists in the parent folder")
        return attrs

    def create(self, validated_data):
        folder = validated_data.get('folder')
        file = validated_data.get('file')
        path: Path = Path(settings.MEDIA_ROOT).joinpath(folder.get_folder_path()).joinpath(file.name)
        if path.exists():
            new_name = path.stem + '.tmp'
            new_path = path.with_name(new_name)
            path.rename(new_path)
            os.remove(new_path)
        return super(FileSerializers, self).create(validated_data)

    class Meta(object):
        model = File
        fields = ('id', 'folder', 'file', 'path', 'file_name', 'file_type', 'modified', 'created', 'url')
        extra_kwargs = dict(
            file_name=dict(read_only=True),
            file_type=dict(read_only=True)
        )


class UpdateFileNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('file_name',)
        extra_kwargs = {'file_name': {'required': True}}

    def update(self, instance, validated_data):

        new_name = validated_data.get('file_name')
        original_file_name = Path(instance.file.name)
        if instance.file_name != new_name:
            if not new_name.endswith(Path(instance.file.name).suffix):
                new_name += original_file_name.suffix
            instance.file.name = os.path.join(os.path.dirname(instance.file.name), new_name)
            instance.save()
        previous_name = instance.tracker.previous('file_name')
        if previous_name:
            previous_path = Path(*Path(instance.file.name).parts[:-1]).joinpath(previous_name)
            if previous_path.exists():
                previous_path.rename(new_name)

        validated_data.update(dict(file_name=Path(new_name).stem))
        return super(UpdateFileNameSerializer, self).update(instance, validated_data)


class LeftOverImageSerializer(serializers.ModelSerializer):
    """
    Example of Polygon with x = 1, y=1 and w=200 and h=200:
    the corners will be:
    {"coordinates": [[1, 1], [201, 1], [201, 201], [1, 201], [1, 1]], "type": "Polygon"}
    """
    id = HashidSerializerCharField(read_only=True, required=False)
    url = serializers.SerializerMethodField()

    def get_url(self, obj) -> str:
        return self.context.get('request').build_absolute_uri(
            reverse("storages:leftover-detail", kwargs=dict(pk=obj.pk)))

    class Meta(object):
        model = LeftOverImage
        fields = '__all__'
        extra_kwargs = dict(
            corners=dict(
                required=False,
                help_text="This is used to input the corners in polygon format, where each fild is normalized. "
                          "This is Optional"),
            x=dict(required=False),
            y=dict(required=False),
            width=dict(required=False),
            height=dict(required=False),
            batch=dict(help_text="Used to group images into groups, this feature can be useful in image processing.")
        )

    def validate(self, attrs: dict):
        corners = attrs.get('corners', None)
        x = attrs.get('x', None)
        y = attrs.get('y', None)
        width = attrs.get('width', None)
        height = attrs.get('height', None)
        to_validate = dict(x=x, y=y, width=width, height=height)
        if corners is None:
            for key in list(to_validate.keys()):
                if to_validate.get(key) is None:
                    raise serializers.ValidationError({key: [f"The {key} value must be set."]})

            corners = create_polygon(x, y, width, height)
        else:
            if not isinstance(corners, dict):
                raise serializers.ValidationError(dict(corners=["Invalid type"]))
            coord = corners.get("coordinates")
            if coord is None:
                raise serializers.ValidationError(dict(corners=["The corners must have the coordinates attr."]))
            if not isinstance(coord, list):
                raise serializers.ValidationError(dict(corners=["The coordinates must be a list of tuples"]))
            x_max = max(coord, key=lambda point: point[0])
            y_max = max(coord, key=lambda point: point[1])
            x_min = min(coord, key=lambda point: point[0])
            y_min = min(coord, key=lambda point: point[1])
            x = x_min[0]
            y = y_min[1]
            width = abs(x - x_max[0])
            height = abs(y - y_max[0])
        attrs.update(dict(x=x, y=y, width=width, height=height, corners=corners))
        return attrs


class LeftOverCornersUpdate(serializers.Serializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    corners = serializers.JSONField(required=True)


class ManyFilesSerializer(serializers.Serializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    folder = PrimaryKeyRelatedFieldHashed(library="bucket", model=Folder)

    def __init__(self, *args, **kwargs):
        file_fields = kwargs.pop('file_fields', None)
        super().__init__(*args, **kwargs)
        if file_fields:
            field_update_dict = {field: serializers.FileField(required=False, write_only=True) for field in file_fields}
            self.fields.update(**field_update_dict)

    def create(self, validated_data):
        validated_data_copy = validated_data.copy()
        validated_files = []
        files = list()
        for key, value in validated_data_copy.items():
            if isinstance(value, InMemoryUploadedFile):
                validated_files.append(value)
                validated_data.pop(key)
        for file in validated_files:
            data = validated_data.copy()
            data.update(dict(folder=str(data.get('folder').id)))
            data.update(dict(file=file))
            serializer = FileSerializers(data=data, context=self.context)
            serializer.is_valid(raise_exception=True)
            files.append(serializer.save())
        if not files:
            raise serializers.ValidationError("No file found in the payload!")
        return files[0]


def validate_file_path(value):
    if not os.path.isfile(value):
        raise serializers.ValidationError("Invalid file path. No file found at the provided location.")
    return value


class CreateFileFromPathSerializer(serializers.Serializer):
    file_path = serializers.CharField()
    folder = PrimaryKeyRelatedFieldHashed(library="bucket", model=Folder)

    def get_url(self, obj) -> str:
        return self.context.get('request').build_absolute_uri(reverse("storages:file-detail", kwargs=dict(pk=obj.pk)))

    def create(self, validated_data):
        file_path = validated_data['file_path']
        folder = validated_data['folder']
        file_name, file_type = os.path.splitext(os.path.basename(file_path))
        with open(file_path, 'rb') as file:
            file_instance = File.objects.create(
                file_name=file_name,
                file_type=file_type,
                file=DjangoFile(file.read()),  # Assumes Django has access to the file system
                folder=folder
            )
        return file_instance
