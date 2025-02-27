from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.models import Site
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.encoding import force_text
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from rest_framework.request import Request

from utilities.constants import TokenValidationResponses
from utilities.tokens import accountActivationTokenGenerator
from urllib.parse import urlparse, urlunparse

User = get_user_model()


def get_profile_str(user: User):
    return User.Roles(user.role).value


def get_domain(url: str) -> str:
    parsed_url = urlparse(url)
    parsed_url = parsed_url._replace(path='')
    new_url = urlunparse(parsed_url)
    return new_url.__str__()


def get_portal_link() -> str:
    """
    Retrieves the portal link for the reset password functionality.

    Returns:
        str: The portal link.

    Description:
        This function filters the Site objects based on the name provided in the settings,
        and if any matching Site exists and the REDIRECT_TO_FRONT flag is set in the settings,
        it retrieves the first matching Site's domain and returns it as the portal link for the reset password.
        If no matching Site is found or the REDIRECT_TO_FRONT flag is not set, an empty string is returned.
    """
    site_sets: QuerySet = Site.objects.filter(name=settings.SITE_RESET_PASSWORD_DOMAIN_NAME)
    if site_sets.exists() and settings.REDIRECT_TO_FRONT:
        site: Site = site_sets.first()
        return get_domain(site.domain)
    return ""


def get_activation_link(request: Request, user: User) -> str:
    """
    This function generates a link for activating an account for a user. This link includes a unique token that is
    generated using the user's primary key and a secret key. The user can click on this link to activate their account.

    :param request: Django Request object
    :type request: Request
    :param user: User object
    :type user: User
    :return: A string representing the link for activating the account.
    :rtype: str
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = accountActivationTokenGenerator.make_token(user=user)
    site_sets: QuerySet = Site.objects.filter(name=settings.SITE_ACTIVATION_DOMAIN_NAME)
    if site_sets.exists() and settings.REDIRECT_TO_FRONT:
        site: Site = site_sets.first()
        return f"{site.domain}?uidb64={uidb64}&token={token}&profile={get_profile_str(user)}"
    uri = reverse("users:activate", kwargs=dict(uidb64=uidb64, token=token))
    return request.build_absolute_uri(uri)


def get_reset_password_link(request: Request, user: User) -> str:
    """
    This function generates a link for resetting the password for a user. It takes in a Django Request object and a
    User object as arguments. First, it creates a URL-safe base64 encoded string of the user's primary key (uidb64).
    It then generates a token using Django's built-in PasswordResetTokenGenerator class. It is then checked if site
    object exist and if redirect to front is true, it will return the link with the domain name and token,
    otherwise it will return the full URL by calling request.build_absolute_uri() on the reverse function with the
    name of the url and passing in the uidb64 and token as keyword arguments. Returns a string representing the link
    for resetting the password.

    :param request: Django Request object
    :type request: Request
    :param user: User object
    :type user: User
    :return: A string representing the link for resetting the password.
    :rtype: str

    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user=user)
    site_sets: QuerySet = Site.objects.filter(name=settings.SITE_RESET_PASSWORD_DOMAIN_NAME)
    if site_sets.exists() and settings.REDIRECT_TO_FRONT:
        site: Site = site_sets.first()
        return f"{site.domain}?uidb64={uidb64}&token={token}&profile={get_profile_str(user)}"
    return request.build_absolute_uri(reverse("users:reset-password-new", kwargs=dict(uidb64=uidb64, token=token)))


def validate_activation_token(uidb64: str, token: str) -> TokenValidationResponses:
    """
    Validate an account activation token for a user.

    This function takes in an uidb64 string, which is the primary key of the user, and a token string, and it checks
    if the provided token is valid for the user.

    The uidb64 string is decoded and used to query the User model to check if the user exists. If the user does not
    exist, it returns "INVALID". If the user exists but is already active, it returns "NO_EFFECT". If the user exists
    and is not active, it checks if the token is valid using the accountActivationTokenGenerator.check_token method.
    If the token is not valid, it returns "HAS_EXPIRED". If the token is valid, it sets the user's is_active field to
    True and saves the user, then returns "SUCCESS".

    :param uidb64: a string that is the primary key of the user
    :type uidb64: str
    :param token: a string that is the token to be validated
    :type token: str
    :return: a TokenValidationResponses Enum that indicates the status of the token validation.
    :rtype: TokenValidationResponses
    """
    try:
        pk = force_text(urlsafe_base64_decode(uidb64))
        user_set: QuerySet = User.objects.filter(pk=pk)
        if not user_set.exists():
            return TokenValidationResponses.INVALID
        user = user_set.first()
        if user.is_active:
            return TokenValidationResponses.NO_EFFECT
        valid_token = accountActivationTokenGenerator.check_token(user=user, token=token)
        if not valid_token:
            return TokenValidationResponses.HAS_EXPIRED
        user.is_active = True
        user.save()
        return TokenValidationResponses.SUCCESS
    except DjangoUnicodeDecodeError:
        return TokenValidationResponses.INVALID


def validate_reset_password_token(uidb64: str, token: str, new_password: str) -> TokenValidationResponses:
    """
    Validate a password reset token for a user.

    This function takes in an uidb64 string, which is the primary key of the user, and a token string, and it checks
    if the provided token is valid for the user.

    The uidb64 string is decoded and used to query the User model to check if the user exists. If the user does not
    exist, it returns "INVALID". If the user exists, it checks if the token is valid using the
    PasswordResetTokenGenerator().check_token method. If the token is not valid, it returns "HAS_EXPIRED" . If the
    token is valid but the user is already inactive, it returns "NO_EFFECT".

    "NO_EFFECT" status is returned if user is already inactive and the token is valid, it means that the user account
    has been deactivated and the token cannot be used to reset the password.

    :param new_password: a string that is the  raw password of the user
    :type new_password: str
    :param uidb64: a string that is the primary key of the user
    :type uidb64: str
    :param token: a string that is the token to be validated
    :type token: str
    :return: a TokenValidationResponses Enum that indicates the status of the token validation.
    :rtype: TokenValidationResponses
    """
    try:
        pk = smart_str(urlsafe_base64_decode(uidb64))
        user_set: QuerySet = User.objects.filter(pk=pk)
        if not user_set.exists():
            return TokenValidationResponses.INVALID
        user: User = user_set.first()
        valid_token = PasswordResetTokenGenerator().check_token(user, token)
        if not valid_token:
            return TokenValidationResponses.HAS_EXPIRED
        if not user.is_active:
            user.set_password(raw_password=new_password)
            user.save()
            return TokenValidationResponses.NO_EFFECT_ON_ACTIVATION
        user.is_active = True
        user.set_password(raw_password=new_password)
        user.save()
        return TokenValidationResponses.SUCCESS
    except DjangoUnicodeDecodeError:
        return TokenValidationResponses.INVALID
