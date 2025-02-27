from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.query import QuerySet
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from utilities.links import validate_activation_token, validate_reset_password_token
from utilities.permissions import HasConnection, ModelPermissions, IsResourceOwner, GetCustomerIDPermission
from utilities.serializers import SetNewPasswordSerializer, ResetPasswordSerializer, ResendActivationSerializer, \
    GetCustomerSerializer
from utilities.signals import user_registered
from utilities.views import UserInterfaceViewSet
from emailManager.tasks import send_reset_password_email_task, send_confirmation_email_task
from . import models
from . import serializers


class CustomerViewSet(UserInterfaceViewSet):
    permission_classes = [IsAuthenticated, HasConnection, ModelPermissions]
    queryset = models.CustomerProfile.objects.all()
    serializer_class = serializers.CustomerSerializer
    register_serializer_class = serializers.RegisterCustomerSerializer
    
    def get_serializer_class(self):
        if self.action == "change_tos":
            return serializers.ChangeTosSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsResourceOwner])
    def change_tos(self, request, pk=None):
        profile = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_tos = serializer.validated_data.get('tos')
        profile.tos = new_tos
        profile.save()
        return Response(data=dict(detail="TOS has been updated!"), status=status.HTTP_200_OK)

    def get_queryset(self) -> QuerySet:
        queryset: QuerySet = super(CustomerViewSet, self).get_queryset()
        if self.request.user.is_customer:
            queryset = queryset.filter(user__username=self.request.user.username)
        return queryset


class OrganizationViewSet(UserInterfaceViewSet):
    permission_classes = [IsAuthenticated, HasConnection, ModelPermissions]
    queryset = models.OrganizationProfile.objects.all()
    serializer_class = serializers.OrganizationSerializer
    register_serializer_class = serializers.RegisterOrganizationSerializer


class WorkerViewSet(UserInterfaceViewSet):
    permission_classes = [IsAuthenticated, HasConnection, ModelPermissions]
    queryset = models.WorkerProfile.objects.all()
    serializer_class = serializers.WorkerSerializer
    register_serializer_class = serializers.RegisterWorkerSerializer


class SignupView(GenericAPIView):
    permission_classes = (IsAuthenticated, HasConnection)
    queryset = models.CustomerProfile.objects.all()
    serializer_class = serializers.SingUpSerializer

    def post(self, request):
        customer_serializer = self.serializer_class(data=request.data)
        customer_serializer.is_valid(raise_exception=True)
        customer = customer_serializer.save()
        user_registered.send(sender=self.__class__, user=customer.user, request=self.request)
        return Response(customer_serializer.data, status=status.HTTP_201_CREATED)


class ActivateUserView(APIView):

    def get(self, request: Request, uidb64: str, token: str):
        from rest_framework.response import Response
        response = validate_activation_token(uidb64=uidb64, token=token)
        site_set: QuerySet = Site.objects.filter(name=settings.SITE_ACTIVATION_DOMAIN_NAME)
        if site_set.exists() and settings.REDIRECT_TO_FRONT:
            site: Site = site_set.first()
            redirect_url = site.domain
            redirect_url += f"{response.value[1]}"
            return redirect(redirect_url)
        return Response(response.value[1], status=response.value[0])


class AddressView(ModelViewSet):
    permission_classes = [IsAuthenticated, HasConnection]
    queryset = models.Address.objects.all()
    serializer_class = serializers.AddressSerializer

    def get_queryset(self) -> QuerySet:
        queryset: QuerySet = super(AddressView, self).get_queryset()
        if self.request.user.is_customer:
            address = self.request.user.customer.address
            delivery_address = self.request.user.customer.delivery_address
            queryset = queryset.filter(id=address.id) | queryset.filter(id=delivery_address.id)
        return queryset


class ResendActivation(GenericAPIView):
    permission_classes = (AllowAny, HasConnection)
    serializer_class = ResendActivationSerializer

    def post(self, request: Request):
        serialized_data: ResendActivationSerializer = self.get_serializer(data=request.data)
        serialized_data.is_valid(raise_exception=True)
        email = serialized_data.data.get('email', '')
        user_set: QuerySet = models.User.objects.filter(email=email)
        if user_set.exists():
            user: models.User = user_set.first()
            if not user.is_active:
                send_confirmation_email_task(request, user=user)
        return Response({'success': 'We have sent you a link to activate your account'}, status=status.HTTP_200_OK)


class ResetPasswordView(GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request: Request):
        serialized_data: ResetPasswordSerializer = self.get_serializer(data=request.data)
        serialized_data.is_valid(raise_exception=True)
        try:
            email = serialized_data.data.get('email', '')
            users = models.User.objects.filter(email=email)
            if users.exists():
                send_reset_password_email_task(request=request, user=users.first())
        except Exception as e:
            raise e

        return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)

    class Meta:
        verbose_name = "Reset Password"


class SetNewPassword(GenericAPIView):
    """
        This endpoint handles the validation of reset password tokens.

        It inherits from APIView, which is a generic view provided by Django REST framework. The class implements a
        single POST method, which is used to validate a token passed as part of the URL.

        To use this endpoint, the frontend application would need to make a GET request to the endpoint with the uidb64
        and token as part of the URL. The get method takes in two arguments: request, uidb64, token. request is the
        standard request object passed in by Django, uidb64 and token are passed as part of the URL.

        When called, the get method calls a helper function validate_reset_password_token() which validates the token
        passed in. It then creates a dictionary data that contains the message from the validation response, as well as
        the uidb64 and token passed in the URL.

        The method then returns a Response object, with the message from the validation response as the first argument
        and the status code from the validation response as the second argument. The frontend application can check the
        status code of the response, if it is 200, it means the token is valid and the user is allowed to change their
        password, otherwise it means the token is invalid and the user is not allowed to change their password.
        """
    serializer_class = SetNewPasswordSerializer

    def post(self, request: Request, uidb64: str, token: str):
        """
        Handles the post request to reset a user's password.

        :param request: (Request) The request object containing the new password data.
        :type request: Request
        :param uidb64: (str) The base64 encoded user ID.
        :type uidb64: str
        :param token: (str) The password reset token.
        :type token: str
        :return: (Response) A response object with the message and status code returned by the
         validate_reset_password_token function.
        :rtype: Response
        """
        serialized: SetNewPasswordSerializer = self.get_serializer(data=request.data)
        serialized.is_valid(raise_exception=True)
        password = serialized.validated_data.get('password')
        response = validate_reset_password_token(uidb64=uidb64, token=token, new_password=password)
        return Response(response.value[1], status=response.value[0])


class GetCustomerAPIView(GenericAPIView):
    permission_classes = (GetCustomerIDPermission | IsAdminUser, HasConnection)
    serializer_class = GetCustomerSerializer

    def post(self, request: Request, **kwargs) -> Response:
        """
        Handles the post request to reset a user's password.

        :param request: (Request) The request object containing the new password data.
        :type request: Request
        :return: (Response) A response object with the message and status code returned by the
         validate_reset_password_token function.
        :rtype: Response
        """
        serialized: GetCustomerSerializer = self.get_serializer(data=request.data)
        serialized.is_valid(raise_exception=True)
        email: QuerySet = serialized.validated_data.get("email")
        customers: QuerySet = models.CustomerProfile.objects.filter(user__email=email)
        data = dict(detail="No customer found", status=status.HTTP_400_BAD_REQUEST, ok=False)
        if customers.exists():
            data = dict(customer=customers.first().id.__str__(), status=status.HTTP_200_OK, ok=True)
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
