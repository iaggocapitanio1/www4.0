from rest_framework import serializers
import re


class CheckSerializer(serializers.Serializer):
    field = serializers.ChoiceField(choices=['username', 'email', 'vat'], required=True)
    value = serializers.CharField(max_length=100, required=True, )

    @staticmethod
    def get_value_regex(obj):
        if obj['field'] == 'username':
            return r'^[a-zA-Z0-9]+$'
        elif obj['field'] == 'email':
            return r'^\S+@\S+\.\S+$'
        elif obj['field'] == 'vat':
            return r'^\d{9}$'
        else:
            return r'.*'

    def validate_value(self, value):
        regex = self.get_value_regex(self.initial_data)
        if not re.match(regex, value):
            raise serializers.ValidationError("Invalid format")
        return value
