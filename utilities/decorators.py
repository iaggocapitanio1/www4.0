from functools import wraps
from typing import Callable, List

import requests
import re
from django.conf import settings
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from .exceptions import OrionSystemOutOfService, OrionWrongURI


def verify_orion_connection(func: Callable) -> Callable:
    def wrapper(self, request, *args, **kwargs):
        try:
            requests.get(url=settings.ORION_ENTITIES, headers=settings.ORION_HEADERS)
            return func(self, request, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()

    return wrapper


def user_has_orion_permission(permission: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if request.user:
                if not request.user.has_orion_perm(permission):
                    raise PermissionDenied
            else:
                return func(self, request, *args, **kwargs)
            return func(self, request, *args, **kwargs)

        return wrapper

    return decorator


def check_uri(fn: Callable) -> Callable:
    def wrapper(self, request, pk, *args, **kwargs):
        if not self.entity_type.lower() == pk.split(":")[2].lower():
            raise OrionWrongURI()
        return fn(self, request, pk, *args, **kwargs)

    return wrapper


def check_uri_from_request(fn: Callable) -> Callable:
    def wrapper(self, request, *args, **kwargs):
        data = request.data

        # Check if the request data is a list of objects
        if isinstance(data, List):
            # Extract the ids from the list
            ids = [obj.get('id') for obj in data]

            # Check if all ids are present and valid
            for id in ids:
                if id is None:
                    raise OrionWrongURI("Request data must contain an 'id' key.")
                # Check if the id follows the URN pattern
                urn_pattern = r"^urn:[a-zA-Z0-9][a-zA-Z0-9-]{0,31}:[a-zA-Z0-9()+,\-.:=@;$_!*'%/?#]+$"
                if not re.match(urn_pattern, id):
                    raise OrionWrongURI("Invalid URN pattern for the 'id' value.")
                if not self.entity_type.lower() == id.split(":")[2].lower():
                    raise OrionWrongURI("Entity type in the URI does not match the expected entity type.")
        else:
            # Check if the request data has a key "id"
            pk = data.get('id', None)
            if pk is None:
                raise OrionWrongURI("Request data must contain an 'id' key.")
            # Check if the id follows the URN pattern
            urn_pattern = r"^urn:[a-zA-Z0-9][a-zA-Z0-9-]{0,31}:[a-zA-Z0-9()+,\-.:=@;$_!*'%/?#]+$"
            if not re.match(urn_pattern, pk):
                raise OrionWrongURI("Invalid URN pattern for the 'id' value.")
            if not self.entity_type.lower() == pk.split(":")[2].lower():
                raise OrionWrongURI("Entity type in the URI does not match the expected entity type.")

        return fn(self, request, *args, **kwargs)

    return wrapper


def check_api_connection(func):
    def wrapper(self, request, *args, **kwargs):
        try:
            requests.get(url=settings.ORION_ENTITIES, headers=settings.ORION_HEADERS)
            return func(self, request, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()

    return wrapper


def customer_profile_exists(view_func):
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        from users.models import CustomerProfile
        data = request.data
        try:
            order_by = data.get('orderBy').get('object')
            pk = order_by.split(':')[-1]
            CustomerProfile.objects.get(pk=pk)
        except Exception as error:
            raise ValidationError(f"The payload doesn't contain a correct user: {error}")
        return view_func(self, request, *args, **kwargs)

    return _wrapped_view


def skip_signal():
    def _skip_signal(signal_func):
        @wraps(signal_func)
        def _decorator(sender, instance, created, **kwargs):
            if hasattr(instance, 'skip_signal'):
                return None
            return signal_func(sender, instance, created, **kwargs)

        return _decorator

    return _skip_signal
