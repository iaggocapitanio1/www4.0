from django.db import models


class AddressManager(models.Manager):
    def get_queryset(self):
        return super(AddressManager, self).get_queryset()

    def create_address(self, streetAddress='', postalCode='', addressLocality='', addressRegion='', addressCountry=''):
        address = self.create(streetAddress=streetAddress,
                              postalCode=postalCode,
                              addressLocality=addressLocality,
                              addressRegion=addressRegion,
                              addressCountry=addressCountry)
        return address
