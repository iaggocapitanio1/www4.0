from enum import Enum
from vies.types import VIES_OPTIONS
from rest_framework import status

from enum import Enum, unique


@unique
class FurnitureType(Enum):
    GROUP = 'group'
    SUBGROUP = 'subGroup'
    FURNITURE = 'furniture'
    ACCESSORY = 'accessory'


    def __str__(self):
        return self.value.__str__()


class TokenValidationResponses(Enum):
    """
    This class defines an Enum with string values to be used as responses when validating a token.

    Attributes:
    SUCCESS (int, str): Tuple of the response code and message returned when the token is valid.
    NO_EFFECT (int, str): Tuple of the response code and message returned when the token has no effect.
    HAS_EXPIRED (int, str): Tuple of the response code and message returned when the token is expired.
    INVALID (int, str): Tuple of the response code and message returned when the token is invalid.
    """
    SUCCESS = status.HTTP_200_OK, "The token is valid. The Operation has occurred successfully."
    NO_EFFECT = status.HTTP_202_ACCEPTED, "Token has no effect."
    NO_EFFECT_ON_ACTIVATION = status.HTTP_200_OK, "Token has no effect on activation but password was reset."
    HAS_EXPIRED = status.HTTP_400_BAD_REQUEST, "Token has expired, it's not valid anymore."
    INVALID = status.HTTP_401_UNAUTHORIZED, "Token is invalid. The Operation has failed. "


COUNTRY = sorted((("", "COUNTRY TAX ID COUNTRY"),) + tuple((key, value[0]) for key, value in VIES_OPTIONS.items()))

RESOURCES = ['assembly', 'budget', 'consumable', 'expedition', 'machine', 'organization', 'owner', 'part', 'project',
             'worker']
