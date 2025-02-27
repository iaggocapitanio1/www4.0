import json
from typing import List

import requests
import requests_auth
from django.conf import settings
from rest_framework import views, status, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from utilities.client import oauth
from utilities.exceptions import OrionSystemOutOfService, AuthenticationFiware
from utilities.functions import generate_urn_identifier
from .decorators import check_uri, check_uri_from_request
from .functions import update_headers
from .permissions import HasConnection


class OrionInterfaceView(views.APIView):
    permission_classes = [permissions.IsAuthenticated | TokenHasReadWriteScope, HasConnection]
    entity_type = 'Owner'
    url = settings.ORION_ENTITIES
    orion_headers = settings.ORION_HEADERS
    special_fields = ["belongsTo", "orderBy", "id", "type"]

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user is None:
            return True
        if user.is_customer:
            if not payload.get('orderBy').get('object'):
                return payload.get('orderBy') == generate_urn_identifier(_type="Owner", uid=user.customer.pk)
            return payload.get('orderBy').get('object') == generate_urn_identifier(_type="Owner", uid=user.customer.pk)
        return True

    def detail_url(self, uid):
        if self.url.endswith('/'):
            return self.url + f"{uid}/"
        return self.url + f"/{uid}/"

    def check_params(self, params: dict) -> dict:
        for key in self.special_fields:
            params.pop(key, None)
        return params

    def check_data(self, data: dict):
        _type = data.get("type", None)
        if _type is not None:
            data.update(dict(type=self.entity_type))
        return data

    def generate_params(self, user):
        params = dict()
        if user is None:
            return dict(type=self.entity_type)
        if user.is_admin or user.is_worker:
            params = dict(type=self.entity_type)
        elif user.is_customer:
            params = dict(id=generate_urn_identifier(_type=self.entity_type, uid=user.customer.pk))
        return params

    def get_object(self, pk, params=None) -> requests.Response:
        if params:
            params = self.check_params(params)
            return requests.get(url=self.detail_url(pk), headers=settings.ORION_HEADERS, params=params, auth=oauth)
        return requests.get(url=self.detail_url(pk), headers=settings.ORION_HEADERS, auth=oauth)


class OrionCreateMixin(object):
    @check_uri_from_request
    def post(self, request: Request) -> Response:
        results = list()
        url = settings.ORION_ENTITIES
        try:
            datas = request.data
            if isinstance(datas, List):

                url = url.replace('/entities', '')
                url += "/entityOperations/create"

                for d in datas:
                    results.append(self.check_data(data=d))
                data = results
            else:
                data = self.check_data(data=datas)
            data_json = json.dumps(data).encode('utf-8')
            response = requests.post(url=url, auth=oauth, data=data_json,
                                     headers=settings.ORION_HEADERS)
            if response.status_code == status.HTTP_201_CREATED:
                if isinstance(datas, List):
                    response_data = response.json()
                else:
                    response_data = data
                return Response(response_data, status=response.status_code, headers=update_headers(response.headers))
            return Response(response.json(), status=response.status_code, headers=update_headers(response.headers))
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()
        except requests_auth.errors.InvalidGrantRequest:
            raise AuthenticationFiware


class OrionListMixin(object):

    def get(self, request: Request):
        params = self.check_params(self.request.query_params.copy())
        params.update(self.generate_params(user=request.user))
        try:
            response: requests.Response = requests.get(url=self.url, headers=settings.ORION_HEADERS, auth=oauth,
                                                       timeout=5,
                                                       params=params)
            if response.status_code == status.HTTP_200_OK:
                return Response(response.json(), status=status.HTTP_200_OK, headers=update_headers(response.headers))
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return Response(response.json(), status=status.HTTP_404_NOT_FOUND,
                                headers=update_headers(response.headers))
            return Response(data=dict(message="No entity found", ok=False, status=404),
                            status=status.HTTP_404_NOT_FOUND)
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()
        except requests_auth.errors.InvalidGrantRequest:
            raise AuthenticationFiware


class OrionRetrieveMixin(object):
    @check_uri
    def get(self, request: Request, pk):
        try:
            params = self.check_params(request.query_params.copy())
            response = self.get_object(pk, params)
            if response.status_code == status.HTTP_200_OK:
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    data = response.content.decode('unicode-escape')  # Decode the response data
                    return Response(json.loads(data), status=response.status_code)
                else:
                    return Response(data=dict(message=f"Invalid content type: {content_type}", ok=False, status=400),
                                    status=status.HTTP_400_BAD_REQUEST,
                                    headers=update_headers(response.headers))
            return Response(data=dict(message="Entity not found", ok=False, status=404),
                            status=status.HTTP_404_NOT_FOUND,
                            headers=update_headers(response.headers))
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()
        except requests_auth.errors.InvalidGrantRequest:
            raise AuthenticationFiware()


class OrionDeleteMixin(object):
    @check_uri
    def delete(self, request: Request, pk: str):
        try:
            data = self.get_object(pk)
            response = requests.delete(url=self.detail_url(uid=pk), headers=settings.ORION_HEADERS, auth=oauth)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return Response({}, status=status.HTTP_200_OK, headers=update_headers(response.headers))
            return Response(dict(message="No entity found!", ok=False, status=status.HTTP_404_NOT_FOUND),
                            status=status.HTTP_404_NOT_FOUND, headers=update_headers(response.headers))
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()
        except requests_auth.errors.InvalidGrantRequest:
            raise AuthenticationFiware


class OrionUpdateMixin(object):

    @staticmethod
    def remove_protected_attrs(data: dict, user) -> dict:
        data.pop("id", None)
        data.pop("type", None)
        if user is not None:
            if not user.is_admin and not user.is_worker:
                data.pop("orderBy", None)
                data.pop("belongsTo", None)
                data.pop("approvedDate", None)
                data.pop("executedIn", None)
                data.pop("executedBy", None)
                data.pop("amount", None)
                data.pop("name", None)
                data.pop("status", None)
        return data

    @check_uri
    def patch(self, request, pk):
        try:
            data: dict = self.check_data(data=request.data)
            data = self.remove_protected_attrs(data, user=request.user)
            response = requests.patch(url=self.detail_url(uid=pk) + "attrs", data=json.dumps(data),
                                      headers=settings.ORION_HEADERS,
                                      auth=oauth)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                response = requests.get(self.detail_url(uid=pk), headers=settings.ORION_HEADERS, auth=oauth)
                return Response(response.json(),
                                status=response.status_code,
                                headers=update_headers(response.headers)
                                )
            return Response(response.json(), status=status.HTTP_400_BAD_REQUEST,
                            headers=update_headers(response.headers))
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()
        except requests_auth.errors.InvalidGrantRequest:
            raise AuthenticationFiware


class OrionCreateAttrsMixin(object):
    @staticmethod
    def remove_protected_attrs(data: dict, user) -> dict:
        data.pop("id", None)
        data.pop("type", None)
        if not user.is_admin and not user.is_worker:
            data.pop("orderBy", None)
            data.pop("belongsTo", None)
            data.pop("approvedDate", None)
            data.pop("executedIn", None)
            data.pop("executedBy", None)
            data.pop("amount", None)
            data.pop("name", None)
            data.pop("status", None)
        return data

    def post(self, request, pk):
        try:
            data: dict = self.check_data(data=request.data)
            data = self.remove_protected_attrs(data, user=request.user)
            response = requests.post(url=self.detail_url(uid=pk) + "attrs", data=json.dumps(data),
                                     headers=settings.ORION_HEADERS,
                                     auth=oauth)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                response = requests.get(self.detail_url(uid=pk), headers=settings.ORION_HEADERS, auth=oauth)
                return Response(response.json(),
                                status=response.status_code,
                                headers=update_headers(response.headers)
                                )
            return Response(response.json(), status=status.HTTP_400_BAD_REQUEST,
                            headers=update_headers(response.headers))
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()
        except requests_auth.errors.InvalidGrantRequest:
            raise AuthenticationFiware


class OrderByRetrieveMixin(OrionRetrieveMixin):
    @check_uri
    def get(self, request, pk: str):
        response = self.get_object(pk)
        if response.status_code == status.HTTP_200_OK:
            if self.verify_orderBy(payload=response.json(), user=request.user):
                return super(OrderByRetrieveMixin, self).get(request, pk)
        return Response(data=dict(message="Entity not found", ok=False, status=404),
                        status=status.HTTP_404_NOT_FOUND)


class OrderByListMixin(OrionListMixin):

    def generate_params(self, user):
        params = dict()
        if user is None:
            return dict(type=self.entity_type)
        if user.is_admin or user.is_worker:
            params = dict(type=self.entity_type)
        elif user.is_customer:
            params = dict(q=f'orderBy=="{generate_urn_identifier(_type="Owner", uid=user.customer.id)}"',
                          type=self.entity_type)
        params.update(dict(count='true'))
        return params

    def get_params(self, request):
        params = self.check_params(self.request.query_params.copy())
        params.update(self.generate_params(user=request.user))
        return params

    def get(self, request: Request):

        try:
            response: requests.Response = requests.get(url=self.url, headers=settings.ORION_HEADERS, auth=oauth,
                                                       params=self.get_params(request))
            if response.status_code == status.HTTP_200_OK:
                return Response(response.json(), status=status.HTTP_200_OK, headers=update_headers(response.headers))
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return Response(response.json(), status=status.HTTP_404_NOT_FOUND,
                                headers=update_headers(response.headers))
            return Response(data=dict(message="No entity found", ok=False, status=404),
                            status=status.HTTP_404_NOT_FOUND)
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()
        except requests_auth.errors.InvalidGrantRequest:
            raise AuthenticationFiware


class OrderByDeleteMixin(OrionDeleteMixin):
    @check_uri
    def delete(self, request: Request, pk: str):
        try:
            data = self.get_object(pk)
            if data.status_code == status.HTTP_200_OK:
                if self.verify_orderBy(payload=data.json(), user=request.user):
                    return super(OrderByDeleteMixin, self).delete(request, pk)
            return Response(dict(message="No entity found!", ok=False, status=status.HTTP_404_NOT_FOUND),
                            status=status.HTTP_404_NOT_FOUND, headers=update_headers(data.headers))
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()


class OrderByUpdateMixin(OrionUpdateMixin):

    @check_uri
    def patch(self, request: Request, pk: str):
        try:
            data = self.get_object(pk)
            if data.status_code == status.HTTP_200_OK:
                if self.verify_orderBy(payload=data.json(), user=request.user):
                    return super(OrderByUpdateMixin, self).patch(request, pk)
            return Response(dict(message="No entity found!", ok=False, status=status.HTTP_404_NOT_FOUND),
                            status=status.HTTP_404_NOT_FOUND, headers=update_headers(data.headers))
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()
        except requests_auth.errors.InvalidGrantRequest:
            raise AuthenticationFiware


class OrderByCreateAttrsMixin(OrionCreateAttrsMixin):

    def post(self, request: Request, pk: str):
        try:
            data = self.get_object(pk)
            if data.status_code == status.HTTP_200_OK:
                if self.verify_orderBy(payload=data.json(), user=request.user):
                    return super(OrderByCreateAttrsMixin, self).post(request, pk)
            return Response(dict(message="No entity found!", ok=False, status=status.HTTP_404_NOT_FOUND),
                            status=status.HTTP_404_NOT_FOUND, headers=update_headers(data.headers))
        except requests.exceptions.ConnectionError:
            raise OrionSystemOutOfService()
        except requests_auth.errors.InvalidGrantRequest:
            raise AuthenticationFiware
