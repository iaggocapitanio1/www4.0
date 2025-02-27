from rest_framework import serializers
from tags.models import Tag
from users.models import User
from hashid_field.rest import HashidSerializerCharField
from utilities.fields import PrimaryKeyRelatedFieldHashed
from django.shortcuts import reverse
import os


def validate_pdf_file(file):
    if not file.name.lower().endswith('.pdf'):
        raise serializers.ValidationError("Only PDF files are allowed.")
    return file


def validate_excel_file(file):
    if not file.name.lower().endswith('.xlsx'):
        raise serializers.ValidationError("Only xlsx files are allowed.")
    return file


class TagSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    pdf = serializers.FileField(validators=[validate_pdf_file])
    excel = serializers.FileField(validators=[validate_excel_file])
    project_owner = PrimaryKeyRelatedFieldHashed(library='users', model=User)
    instance = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        if 'pdf' in validated_data:
            try:
                if os.path.exists(instance.pdf.path):
                    instance.pdf.delete()
            except ValueError:
                pass
            instance.pdf.delete()
        if 'excel' in validated_data:
            try:
                if os.path.exists(instance.excel.path):
                    instance.excel.delete()
            except ValueError:
                pass
        return super(TagSerializer, self).update(instance, validated_data)

    class Meta:
        model = Tag
        view_name = 'tag'
        fields = ('id', 'project', 'project_owner', 'pdf', 'created', 'modified', 'instance', 'excel')
        extra_kwargs = {
            'id': {'read_only': True},
            'created': {'read_only': True},
            'modified': {'read_only': True},
        }

    def get_fields(self):
        fields = super(TagSerializer, self).get_fields()
        if self.get_action() != "list":
            fields.pop('instance')
        return fields

    def get_request(self):
        return self.context.get('request')

    def get_action(self) -> str:
        return self.context.get('view').action

    def get_instance(self, obj):
        return self.get_request().build_absolute_uri(
            reverse(f"tags:{self.Meta.view_name}-detail", kwargs=dict(pk=obj.id)))


class TagResultSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    pdf = serializers.FileField(validators=[validate_pdf_file])
    tag = PrimaryKeyRelatedFieldHashed(library='tags', model=Tag)
    instance = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        view_name = 'tag-result'
        fields = ('id', 'tag', 'pdf', 'created', 'modified', 'instance')
        extra_kwargs = {
            'id': {'read_only': True},
            'created': {'read_only': True},
            'modified': {'read_only': True},
        }

    def get_fields(self):
        fields = super(TagResultSerializer, self).get_fields()
        if self.get_action() != "list":
            fields.pop('instance')
        return fields

    def get_request(self):
        return self.context.get('request')

    def get_action(self) -> str:
        return self.context.get('view').action

    def get_instance(self, obj):
        return self.get_request().build_absolute_uri(
            reverse(f"tags:{self.Meta.view_name}-detail", kwargs=dict(pk=obj.id)))