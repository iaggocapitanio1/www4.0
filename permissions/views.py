from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth.models import Group as Django_Group
from utilities.permissions import PermissionPermissions, GroupPermissions
from .models import Permission, Group
from .serializers import PermissionsSerializer, GroupSerializer, GroupSerializerExpanded, GroupManagerSerializer


class PermissionsViewSet(ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionsSerializer
    permission_classes = [IsAuthenticated, PermissionPermissions]

    @action(detail=False, methods=['get'])
    def no_pagination(self, request, *args, **kwargs):
        self.pagination_class = None
        return self.list(request, *args, **kwargs)


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    expanded_serializer_class = GroupSerializerExpanded
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    def get_serializer_class(self):
        if self.action == 'expanded':
            return self.expanded_serializer_class
        return self.serializer_class

    @action(detail=False, methods=['get'])
    def no_pagination(self, request, *args, **kwargs):
        self.pagination_class = None
        return self.list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def expanded(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class GroupManagerViewSet(ModelViewSet):
    queryset = Django_Group.objects.all()
    serializer_class = GroupManagerSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
