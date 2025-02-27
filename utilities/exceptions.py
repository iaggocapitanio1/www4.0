from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class OrionSystemOutOfService(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = _('We are having some issues with our Fiware backend, try again later.')
    default_code = 'service_unavailable'


class AuthenticationFiware(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = _('Error to authenticate with Fiware Backend.')
    default_code = 'service_unavailable'


class OrionWrongURI(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("The uri is incorrect, it doesn't match the view endpoint")
    default_code = 'error'


class FileAccess(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("You don't have permission to access this file")
    default_code = 'error'
