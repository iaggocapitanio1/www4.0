from django.db.models.query import QuerySet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from chat.filter import MessageFilterSet
from chat.models import Message
from chat.serializer import MessageSerializer
from utilities.permissions import HasConnection


class MessageViewSet(ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [HasConnection, IsAuthenticated]
    filterset_class = MessageFilterSet

    def get_queryset(self):
        qs: QuerySet = super().get_queryset()
        if self.request.user.is_customer:
            qs = qs.filter(by=self.request.user) | qs.filter(to=self.request.user)
        return qs
