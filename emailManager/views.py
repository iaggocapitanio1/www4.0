from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from emailManager.serialziers import SendEmailSerializer
from users.models import User
from django.db.models.query import QuerySet
from django.core import mail
from django.conf import settings
from utilities.permissions import EmailPermission


class SendEmailViewSet(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser | EmailPermission]
    serializer_class = SendEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipients: list = serializer.validated_data.get("recipients", [])
        subject = serializer.validated_data.get("subject")
        message = serializer.validated_data.get("message")
        html_message = serializer.validated_data.get("html_message")
        recipient_group: str = serializer.validated_data.get("recipient_group", -1)
        users: QuerySet = User.objects.none()
        if recipients:
            users: QuerySet = User.objects.filter(pk__in=[user.pk for user in recipients])
        if recipient_group and recipient_group != -1:
            user_set: QuerySet = User.objects.filter(role=recipient_group)
            users = user_set | users
        to = [user.email for user in users]
        from_email = settings.DEFAULT_FROM_EMAIL
        try:
            mail.send_mail(subject=subject, message=message, html_message=html_message, from_email=from_email,
                           recipient_list=to)
        except Exception as error:
            print(error)
            return Response({"status": "Error", "message": str(error)}, status=500)
        return Response({"status": "Email sent to selected recipients"})
