from django.contrib.auth import get_user_model
from rest_framework import serializers
from chat.models import Message
from utilities.fields import PrimaryKeyRelatedFieldHashed
from hashid_field.rest import HashidSerializerCharField

User = get_user_model()


class PrimaryKeyRelatedFieldHashedBy(PrimaryKeyRelatedFieldHashed):

    def to_internal_value(self, data):
        return super().to_internal_value(data)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.context.get("request").user
        if user.is_customer:
            qs = qs.filter(id=user.id)
        return qs


class PrimaryKeyRelatedFieldHashedTo(PrimaryKeyRelatedFieldHashed):

    def to_internal_value(self, data):
        return super().to_internal_value(data)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.context.get("request").user
        if user.is_customer:
            qs = qs.filter(role=0) | qs.filter(role=1)
        return qs


class MessageSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    to = PrimaryKeyRelatedFieldHashedTo(library='users', model=User, read_only=False)
    by = PrimaryKeyRelatedFieldHashedBy(library='users', model=User, read_only=False)

    class Meta(object):
        model = Message
        fields = '__all__'
