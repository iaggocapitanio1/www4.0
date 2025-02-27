from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import reverse
from hashid_field.rest import HashidSerializerCharField
from localflavor.generic.countries.iso_3166 import ISO_3166_1_ALPHA2_COUNTRY_CODES
from rest_framework import serializers, request
from vies.types import VATIN
from typing import Union
from django.contrib.auth.models import Group as Django_Group
from users.models import Address
from bucket.models import Folder
from permissions.models import Group as OrionGroup
from utilities.fields import PrimaryKeyRelatedFieldHashed
from utilities.functions import generate_password
from .functions import get_postcode_validator

User = get_user_model()


class OrionGroupSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)

    class Meta:
        model = OrionGroup
        fields = [
            'id',
            'name'
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'name': {"read_only": True, },
        }


class DjangoGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Django_Group
        fields = [
            'id',
            'name'
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'name': {"read_only": True, },
        }


class UserSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    permissions = serializers.SerializerMethodField()
    orion_permissions = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    orion_groups = OrionGroupSerializer(many=True, read_only=True)
    groups = DjangoGroupsSerializer(many=True, read_only=True)

    @staticmethod
    def get_role(obj):
        return User.Roles(obj.role).name

    @staticmethod
    def get_orion_permissions(obj):
        return [perm.codename for perm in obj.get_all_orion_permissions()]

    @staticmethod
    def get_permissions(obj):
        return obj.get_all_permissions()

    def get_request(self) -> request.Request:
        return self.context.get('request')

    def get_action(self) -> str:
        return self.context.get('view').action

    def verify_role(self, role) -> bool:
        if self.get_request().user.is_authenticated:
            return self.get_request().user.role == role
        return False

    def is_customer(self) -> bool:
        return self.verify_role(role=User.Roles.CUSTOMER)

    def is_admin(self) -> bool:
        return self.verify_role(role=User.Roles.ADMIN)

    def is_worker(self) -> bool:
        return self.verify_role(role=User.Roles.WORKER)

    def get_extra_kwargs(self) -> dict:
        kwargs = super(UserSerializer, self).get_extra_kwargs()
        if self.get_action() in ['update', 'partial_update']:
            kwargs.update({'email': {'read_only': True}, 'username': {'read_only': True},
                           'role': {'read_only': True}, })
        if not self.get_request().user.is_authenticated:
            kwargs.update({"role": {"read_only": True}, "is_active": {"read_only": True}})
        if self.is_admin():
            kwargs.update({"role": {"read_only": True}, "is_active": {"read_only": False}})
        return kwargs

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'picture',
            'is_active',
            'role',
            'permissions',
            'groups',
            'orion_groups',
            'orion_permissions'

        ]

        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'password_confirm': {'write_only': True, 'style': {'input_type': 'password'}},
            'id': {'read_only': True},
            'picture': {'help_text': 'User`s profile picture.'},
            'is_active': {"read_only": True},
            'role': {"read_only": True,
                     'help_text': 'What kind of user you want to register? roles: 0 - Admin; 1 - Staff; 2 - Client.'},
        }


class RegisterUserSerializer(UserSerializer):
    password_confirm = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    role = User.Roles.WORKER

    def validate(self, attrs):
        attrs = super(RegisterUserSerializer, self).validate(attrs)
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm')
        if password_confirm != password:
            raise serializers.ValidationError({'password_confirm': "Passwords must match"})
        attrs.update(dict(role=self.role))
        return attrs

    def create(self, validated_data):
        validated_data.pop('password')
        user = super().create(validated_data)
        if not settings.CREATE_AS_ACTIVE:
            user.is_active = False
        user.set_password(raw_password=generate_password(username=validated_data.get('username')))
        user.save()
        return user

    class Meta(UserSerializer.Meta):
        fields = getattr(UserSerializer.Meta, 'fields') + ['password', 'password_confirm']


class RegisterOrganizationUserSerializer(RegisterUserSerializer):
    role = User.Roles.ADMIN


class RegisterWorkerUserSerializer(RegisterUserSerializer):
    role = User.Roles.WORKER


class RegisterCustomerUserSerializer(RegisterUserSerializer):
    role = User.Roles.CUSTOMER


class AddressSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    addressCountry = serializers.ChoiceField(choices=ISO_3166_1_ALPHA2_COUNTRY_CODES, required=True)

    def validate(self, attrs):
        country_code = attrs.get('addressCountry')
        postal_code = attrs.get('postalCode')
        if country_code in ISO_3166_1_ALPHA2_COUNTRY_CODES:
            validator = get_postcode_validator(country_code)
            try:
                validator(postal_code)
            except ValidationError as e:
                raise serializers.ValidationError({'postalCode': [e]})
        return attrs

    class Meta:
        model = Address
        fields = '__all__'


class NestedProfileSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    user = UserSerializer()
    nested: list = ['user']

    def get_nested(self) -> list:
        return self.nested

    def create_nested_field(self, field_name: str, validated_data: dict) -> dict:
        field_data = validated_data.pop(field_name)
        field_serializer = self.fields[field_name]
        instance = field_serializer.create(field_data)
        validated_data.update({field_name: instance})
        return validated_data

    def update_nested_field(self, instance, field_name: str, validated_data: dict) -> dict:
        field_data = validated_data.pop(field_name)
        field_serializer = self.fields[field_name]
        field_serializer.update(getattr(instance, field_name), field_data)
        return validated_data

    def update(self, instance, validated_data):
        if self.get_nested():
            for nested_field in self.nested:
                if validated_data.get(nested_field, False):
                    validated_data = self.update_nested_field(instance, nested_field, validated_data)

        return super(NestedProfileSerializer, self).update(instance, validated_data)

    def create(self, validated_data):
        if self.get_nested():
            for nested_field in self.nested:
                validated_data = self.create_nested_field(field_name=nested_field, validated_data=validated_data)
        return super(NestedProfileSerializer, self).create(validated_data)

    @staticmethod
    def check_taxId(taxId: str, isCompany: bool, country=None) -> Union[str, None]:
        """
        This function is used to check the validity of a tax ID (such as a VAT number) based on the provided parameters.
        The taxId parameter is the tax ID to be validated, isCompany is a boolean indicating whether the tax ID belongs
        to a company or an individual, and country is an optional parameter used to specify the country for which the
        tax ID should be validated.

        The function returns a string indicating the validation status of the tax ID. If the tax ID is valid, the
        string "valid" is returned. If the tax ID is invalid, the string "invalid" is returned. If the country provided
        is not supported, the string "unsupported country" is returned.

        This function can be useful for checking the validity of a tax ID before performing any further actions in the
        application, such as creating a new user or billing a customer. It can help ensure that the information
        provided by the user is accurate and can be used for tax or compliance purposes.

        :param taxId: A string representing the tax identification number.
        :param isCompany: A boolean indicating if the taxId belongs to a company.
        :param country: (Optional) A string representing the country of the taxId.
        :return: A string indicating the taxId passed the validation.
        """
        if not taxId:
            return None
        from zeep.exceptions import Fault
        vat = VATIN.from_str(taxId)
        country_code: str = vat.get_country_code()
        # if taxId is None:
        #   raise serializers.ValidationError({"vat": ["Invalid tax ID"]})
        if isCompany:
            if country_code.isalpha():
                vat = VATIN(country_code=country_code, number=vat.get_number())
                try:
                    if vat.is_valid():
                        return vat.__str__()
                except Fault as error:
                    print(f"Micro Service without connection! \n \n {error}")
                    vat.verify()
                    return vat.__str__()
            else:
                if country:
                    vat = VATIN(country_code=country, number=taxId)
                    try:
                        if vat.is_valid():
                            return vat.__str__()
                    except Fault as error:
                        print(f"Micro Service without connection! \n \n {error}")
                        pass
        try:
            vat.verify()
            return vat.__str__()
        except ValidationError:
            if country:
                vat = VATIN(country_code=country, number=taxId)
                try:
                    vat.verify()
                    return vat.__str__()
                except Exception:
                    raise serializers.ValidationError({"vat": ["Invalid tax ID"]})
            else:
                raise serializers.ValidationError({"country": ["You need to choose an Country code"]})

    class Meta(object):
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'password_confirm': {'write_only': True, 'style': {'input_type': 'password'}},
            'id': {'read_only': True},
            'picture': {'help_text': 'User`s profile picture.'},
            'role': {'help_text': 'What kind of user you want to register? roles: 0 - Admin; 1 - Staff; 2 - Client.',
                     'read_only': True},
            'country': {'help_text': 'Value Added Tax (VAT) country of origin'},
        }


class ProfileSerializer(NestedProfileSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    url = serializers.SerializerMethodField()
    user = UserSerializer()
    view_name = "profile"

    def get_request(self):
        return self.context.get('request')

    def get_action(self) -> str:
        return self.context.get('view').action

    def get_url(self, obj):
        return self.get_request().build_absolute_uri(reverse(f"users:{self.view_name}-detail", kwargs=dict(pk=obj.id)))

    class Meta(NestedProfileSerializer.Meta):
        pass


class SingUpUserSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    password_confirm = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    role = User.Roles.CUSTOMER

    def validate(self, attrs):
        attrs = super(SingUpUserSerializer, self).validate(attrs)
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm')
        if password_confirm != password:
            raise serializers.ValidationError({'password_confirm': "Passwords must match"})
        attrs.update(dict(role=self.role))
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        if not settings.CREATE_AS_ACTIVE:
            user.is_active = False
        if password:
            user.set_password(raw_password=password)
            user.save()
        return user

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'picture',
            'password',
            'password_confirm',

        ]

        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'password_confirm': {'write_only': True, 'style': {'input_type': 'password'}},
            'id': {'read_only': True},
            'picture': {'help_text': 'User`s profile picture.'},
            'role': {'help_text': 'What kind of user you want to register? roles: 0 - Admin; 1 - Staff; 2 - Client.'},
            'country': {'help_text': 'Value Added Tax (VAT) country of origin'},
        }


class SingUpUserWithDefaultPasswordSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    role = User.Roles.CUSTOMER

    def validate(self, attrs):
        attrs = super(SingUpUserWithDefaultPasswordSerializer, self).validate(attrs)
        attrs.update(dict(role=self.role))
        return attrs

    def create(self, validated_data):
        username = validated_data.get('username')
        password = generate_password(username=username)
        user = super().create(validated_data)
        if not settings.CREATE_AS_ACTIVE:
            user.is_active = False
        if password:
            user.set_password(raw_password=password)
            user.save()
        return user

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'picture',

        ]

        extra_kwargs = {
            'id': {'read_only': True},
            'picture': {'help_text': 'User`s profile picture.'},
            'role': {'help_text': 'What kind of user you want to register? roles: 0 - Admin; 1 - Staff; 2 - Client.'},
            'country': {'help_text': 'Value Added Tax (VAT) country of origin'},
        }


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=3, required=True)

    class Meta:
        fields = ('email',)


class ResendActivationSerializer(ResetPasswordSerializer):
    pass


class GetCustomerSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=50)

    def validate_user_id(self, attrs):
        attrs = attrs.strip()
        return attrs

    class Meta:
        fields = ['email']
        extra_kwargs = {
            'email': {'write_only': True, 'style': {'input_type': 'email'}},
        }


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=64, style=dict(input_type='password'), required=True,
                                     write_only=True)
    password_confirm = serializers.CharField(min_length=6, max_length=64, style=dict(input_type='password'),
                                             required=True, write_only=True)

    class Meta:
        fields = ('password', 'password_confirm', 'token', 'uidb64')
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'password_confirm': {'write_only': True, 'style': {'input_type': 'password'}},
        }

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        if not (password == password_confirm):
            raise serializers.ValidationError(dict(password_confirm=["The password didn't match!"],
                                                   password=["The password didn't match!"]))
        return super(SetNewPasswordSerializer, self).validate(attrs)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        password = attrs.get('new_password')
        password_confirm = attrs.get('new_password_confirm')
        if not (password == password_confirm):
            raise serializers.ValidationError(dict(password_confirm=["The password didn't match!"],
                                                   password=["The password didn't match!"]))
        return super(ChangePasswordSerializer, self).validate(attrs)


class AvatarSerializer(serializers.Serializer):
    profile = serializers.CharField(max_length=150, read_only=True)
    avatar = serializers.ImageField(allow_null=True,
                                    allow_empty_file=True, required=False, use_url=True)

    class Meta:
        fields = ('avatar', 'profile')


class MeSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True, required=False)
    folders = PrimaryKeyRelatedFieldHashed(library='bucket', model=Folder, many=True, read_only=True)
    permissions = serializers.SerializerMethodField()
    orion_permissions = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    tos = serializers.SerializerMethodField()
    orion_groups = PrimaryKeyRelatedFieldHashed(library='permissions', model=OrionGroup, many=True, read_only=True)

    def get_tos(self, user):
        if hasattr(user, 'customer'):
            return user.customer.tos
        return None

    @staticmethod
    def get_role(obj):
        return User.Roles(obj.role).name

    @staticmethod
    def get_orion_permissions(obj) -> list:
        return [perm.codename for perm in obj.get_all_orion_permissions()]

    @staticmethod
    def get_permissions(obj) -> list:
        return obj.get_all_permissions()

    def get_extra_kwargs(self) -> dict:
        kwargs = super(MeSerializer, self).get_extra_kwargs()
        if not self.context.get('request').user.is_authenticated:
            kwargs.update({"role": {"read_only": True}, "is_active": {"read_only": True}})
        if self.context.get('request').user.is_admin:
            kwargs.update({"role": {"read_only": True}, "is_active": {"read_only": False}})
        return kwargs

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'picture',
            'is_active',
            'role',
            'folders',
            'permissions',
            'orion_permissions',
            'orion_groups',
            'tos'

        ]


class ChangeActivationSerializer(serializers.Serializer):
    active = serializers.BooleanField(default=False)

    class Meta:
        fields = ('active',)
