from django.contrib.auth.models import Group as Django_Group
from hashid_field.rest import HashidSerializerCharField
from rest_framework import serializers
from permissions.models import Permission, Group
from utilities.fields import PrimaryKeyRelatedFieldHashed
from users.models import User


class PermissionsSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)

    class Meta(object):
        model = Permission
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
        }


class AddPermissionsSerializer(serializers.Serializer):
    add_permissions = PrimaryKeyRelatedFieldHashed(many=True, model=Permission, library='permissions', )
    permissions = PermissionsSerializer(read_only=True, many=True)

    class Meta(object):
        fields = '__all__'
        extra_kwargs = dict(
            permissions=dict(read_only=True)
        )


class GroupSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    permissions = PrimaryKeyRelatedFieldHashed(many=True, model=Permission, library='permissions', write_only=True)

    class Meta(object):
        model = Group
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
        }


class AddGroupSerializer(serializers.Serializer):
    add_groups = PrimaryKeyRelatedFieldHashed(many=True, model=Group, library='permissions', )
    groups = GroupSerializer(read_only=True, many=True)

    class Meta(object):
        fields = '__all__'
        extra_kwargs = dict(
            groups=dict(read_only=True)
        )


class DjangoGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Django_Group
        fields = ['id', 'name']


class DjangoUserGroupSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'groups']
        extra_kwargs = {
            'id': {'read_only': True},
        }


class DjangoUserGroupSerializerRead(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    groups = DjangoGroupSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ['id', 'groups']
        extra_kwargs = {
            'id': {'read_only': True},
        }


class GroupSerializerExpanded(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    permissions = PermissionsSerializer(many=True)

    class Meta(object):
        model = Group
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
        }


class GroupManagerSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(queryset=Permission.objects.all(), slug_field='codename', many=True)

    class Meta:
        model = Django_Group
        fields = ['id', 'name', 'permissions']
