from typing import List, Dict, Any
from django.conf import settings
import requests
import inspect
import json
from utilities.client import oauth


class BasePayload(object):
    PROPS_TO_EXCLUDE = ['context', 'headers', 'url', 'id', 'type', 'link_headers']
    RELATIONAL_PROPS = []

    def __init__(self, **kwargs) -> None:
        self.headers = kwargs.get('headers', settings.ORION_HEADERS)
        self.url = kwargs.get('url', settings.ORION_ENTITIES)
        self.type = kwargs.get('type', 'Part')
        self.id = kwargs.get('id', None)

    def validate_props(self, props: list) -> list:
        # if not all(prop in self.get_all_properties() for prop in props) and len(props)!= 0:
        #     raise ValueError('PROPS ARE BAD IMPLEMENTED!')
        return props

    def get_props_to_exclude(self):
        return self.validate_props(props=self.PROPS_TO_EXCLUDE)

    def get_relational_props(self):
        return self.validate_props(props=self.RELATIONAL_PROPS)

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, identifier) -> None:
        self._id = identifier

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, _type) -> None:
        self._type = _type

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers

    @headers.setter
    def headers(self, headers: Dict[str, str]) -> None:
        self._headers = headers

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, url: str) -> None:
        self._url = url

    def get_all_properties(self) -> List[str]:
        return [prop[0] for prop in inspect.getmembers(self.__class__, lambda inst: isinstance(inst, property))]

    def clean_properties(self) -> List[str]:
        props = self.get_all_properties()
        for removable in self.get_props_to_exclude() + self.get_relational_props():
            if removable in props:
                props.remove(removable)
        return props

    @staticmethod
    def create_field(_type: str, value: Any, relationship=False) -> Dict[str, Any]:
        if relationship:
            return dict(type=_type, object=value)
        return dict(type=_type, value=value)

    def body(self) -> dict:
        payload_body = dict(id=self.id, type=self.type)
        for prop in self.clean_properties():
            payload_body[prop] = self.create_field(_type='Property', value=getattr(self, prop))
        # payload_body["@context"] = self.context
        for prop in self.get_relational_props():
            payload_body[prop] = self.create_field(_type='Relationship', value=getattr(self, prop), relationship=True)
        return payload_body

    def partial_body(self) -> dict:
        partial_body = dict()
        actual = self.get(dict(options='keyValues')).json()
        for prop in self.clean_properties():
            value = getattr(self, prop)
            actual_value = actual.get(prop, None)
            if actual_value is not None and not value == actual_value:
                partial_body[prop] = self.create_field(_type='Property', value=value)
        return partial_body

    def json(self):
        return json.dumps(self.body())

    def partial_json(self):
        return json.dumps(self.partial_body())

    def post(self):
        return requests.post(self.url, self.json(), auth=oauth, headers=self.headers)

    def url_with_pk(self):
        if self.url.endswith('/'):
            return self.url + f"{self.id}/"
        return self.url + f"/{self.id}/"

    def get(self, params=None):
        if not params:
            params = {}
        return requests.get(self.url_with_pk(), headers=self.headers, auth=oauth, params=params)

    def patch(self, params=None):
        return requests.patch(self.url_with_pk() + 'attrs/', self.partial_json(), auth=oauth, headers=self.headers,
                              params=params)

    def delete(self):
        return requests.delete(self.url_with_pk(), auth=oauth, headers=self.headers)

    def list(self, params=None):
        return requests.get(self.url, auth=oauth, headers=self.headers, params=params)
