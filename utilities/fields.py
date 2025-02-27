from hashid_field.rest import HashidSerializerCharField
from rest_framework import serializers


class PrimaryKeyRelatedFieldHashed(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        pk_field = kwargs.get('pk_field', None)
        libray = kwargs.pop('library')
        model = kwargs.pop('model')
        if not pk_field and libray and model:
            source_field = f"{libray}.{model.__name__}.id"
            kwargs.update({'pk_field': HashidSerializerCharField(source_field=source_field)})
        self.model = model
        super(PrimaryKeyRelatedFieldHashed, self).__init__(**kwargs)

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model) -> None:
        try:
            assert model
            self._model = model
        except Exception as error:
            ValueError(f"Model attribute can not be None! \n {error}")

    def get_queryset(self):
        return self.model.objects.all()
