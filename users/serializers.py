from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.serializers import ChoiceField
from typing import Union
from users import models
from utilities.constants import COUNTRY
from utilities.fields import PrimaryKeyRelatedFieldHashed
from utilities.serializers import (ProfileSerializer, AddressSerializer, RegisterCustomerUserSerializer,
                                   RegisterWorkerUserSerializer, RegisterOrganizationUserSerializer,
                                   SingUpUserWithDefaultPasswordSerializer, NestedProfileSerializer)


class OrganizationSerializer(ProfileSerializer):
    view_name = "organization"
    nested = ['user']

    class Meta(ProfileSerializer.Meta):
        model = models.OrganizationProfile
        fields = '__all__'


class RegisterOrganizationSerializer(OrganizationSerializer):
    user = RegisterOrganizationUserSerializer()
    country = ChoiceField(choices=COUNTRY, write_only=True, required=False)

    def validate(self, attrs: dict) -> dict:
        country = attrs.pop('country', None)
        tax_id = attrs.get('vat', None)
        tax_id = self.check_taxId(taxId=tax_id, country=country, isCompany=True)
        if self.Meta.model.objects.filter(vat=tax_id).exists():
            raise ValidationError(dict(vat=["The vat number already exists."]))
        attrs.update(dict(vat=tax_id))
        return super().validate(attrs)


class WorkerSerializer(ProfileSerializer):
    view_name = "worker"
    hasOrganization = PrimaryKeyRelatedFieldHashed(library='users', model=models.OrganizationProfile)
    nested = ['user']

    class Meta(ProfileSerializer.Meta):
        model = models.WorkerProfile
        fields = '__all__'


class RegisterWorkerSerializer(WorkerSerializer):
    user = RegisterWorkerUserSerializer()


class CustomerSerializer(ProfileSerializer):
    view_name = "customer"
    nested = ['user', 'address', 'delivery_address']
    address = AddressSerializer()
    delivery_address = AddressSerializer()

    class Meta(ProfileSerializer.Meta):
        model = models.CustomerProfile
        fields = '__all__'


class RegisterCustomerSerializer(CustomerSerializer):
    user = RegisterCustomerUserSerializer()
    country = ChoiceField(choices=COUNTRY, write_only=True)

    def validate_vat(self, vat: Union[str, None]) -> Union[str, None]:
        if vat is not None and self.Meta.model.objects.filter(vat=vat).exists():
            raise ValidationError("The vat is not unique!")
        return vat

    def validate(self, attrs: dict) -> dict:
        country = attrs.pop('country')
        tax_id = attrs.get('vat')
        is_company = attrs.get('isCompany')
        tax_id = self.check_taxId(taxId=tax_id, country=country, isCompany=is_company)
        if tax_id is not None and self.Meta.model.objects.filter(vat=tax_id).exists():
            raise ValidationError(dict(vat=["The vat number already exists."]))
        attrs.update(dict(vat=tax_id))
        return super().validate(attrs)


class SingUpSerializer(NestedProfileSerializer):
    user = SingUpUserWithDefaultPasswordSerializer()
    country = ChoiceField(choices=COUNTRY, write_only=True, required=False)
    address = AddressSerializer()
    delivery_address = AddressSerializer()
    nested = ['user', 'address', 'delivery_address']

    class Meta(object):
        model = models.CustomerProfile
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'country': {'help_text': 'Value Added Tax (VAT) country of origin'},
            'vat': {'help_text': 'Value Added Tax (VAT) is a consumption tax that is applied to nearly all goods and '
                                 'services that are bought and sold for use or consumption in the EU.'},
            'role': {'help_text': 'What kind of user you want to register? roles: 0 - Admin; 1 - Staff; 2 - Client.'},
            'tos': {'help_text': 'This field is used to indicate whether the user has accepted the terms of service, '
                                 'True for accepted and False for not accepted.'},
            'isCompany': {'help_text': 'This info is useful for the vat validation.'}
        }

    def validate(self, attrs: dict) -> dict:
        country = attrs.pop('country', None)
        tax_id = attrs.get('vat', None)
        is_company = attrs.get('isCompany')
        tax_id = self.check_taxId(taxId=tax_id, country=country, isCompany=is_company)
        attrs.update(dict(vat=tax_id))
        if tax_id is not None and self.Meta.model.objects.filter(vat=tax_id).exists():
            raise ValidationError(dict(vat=["The vat number already exists."]))
        return super().validate(attrs)


class ChangeTosSerializer(serializers.Serializer):
    tos = serializers.BooleanField(required=True)
