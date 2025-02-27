import os

from django.db.models.query import QuerySet
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from bucket.models import Folder, File, LeftOverImage
from bucket.serializers import FolderSerializer, FileSerializers, ManyFilesSerializer, LeftOverImageSerializer, \
    LeftOverCornersUpdate, UpdateFileNameSerializer, FolderCreateByEmailSerializer, CreateFileFromPathSerializer
from utilities.exceptions import FileAccess
from utilities.permissions import ModelPermissions, HasConnection
from . import filters


class FolderViewSet(viewsets.ModelViewSet):
    """
    This endpoint provides an interface for handling CRUD operations on Folder objects. It uses the FolderSerializer
    for creating and updating folders, and the FolderSerializerDetail for retrieving and destroying folders.

    If a folder is owned by a user, all its children will also be owned by that user.
    """
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    permission_classes = [HasConnection | TokenHasReadWriteScope,
                          ModelPermissions | IsAdminUser | TokenHasReadWriteScope,
                          IsAuthenticated | TokenHasReadWriteScope]
    filterset_class = filters.FolderFilterSet

    def get_serializer_class(self):
        if self.action == "create_folder_with_email":
            return FolderCreateByEmailSerializer
        return super(FolderViewSet, self).get_serializer_class()

    def get_queryset(self):
        qs: QuerySet = super().get_queryset()
        if self.request.user:
            if self.request.user.is_customer:
                qs = qs.filter(user=self.request.user)
        return qs

    @action(detail=False, methods=['post'])
    def create_folder_with_email(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializers
    batch_files_serializer = ManyFilesSerializer
    permission_classes = [HasConnection | TokenHasReadWriteScope,
                          ModelPermissions | IsAdminUser | TokenHasReadWriteScope,
                          IsAuthenticated | TokenHasReadWriteScope]
    filterset_class = filters.FileFilterSet

    def get_queryset(self):
        qs: QuerySet = super().get_queryset()
        if self.request.user and self.request.user.is_customer:
            qs = qs.filter(folder__user=self.request.user)
        return qs

    def get_serializer_class(self):
        if self.action == 'batch_files':
            return self.batch_files_serializer
        elif self.action == 'update_file_name':
            return UpdateFileNameSerializer
        elif self.action == 'create_from_path':
            return CreateFileFromPathSerializer
        return self.serializer_class

    @action(methods=['post'], detail=False, )
    def batch_files(self, request: Request):
        serializer = self.get_serializer(data=request.data, file_fields=list(request.FILES.keys()))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['patch', 'put'], serializer_class=UpdateFileNameSerializer)
    def update_file_name(self, request, pk=None):
        file = self.get_object()
        serializer = self.get_serializer(file, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        current: File = self.get_object()
        if current.file and os.path.exists(current.file.path):
            os.remove(current.file.path)
        return super().update(request, *args, **kwargs)


class LeftOverImageViewSet(viewsets.ModelViewSet):
    queryset = LeftOverImage.objects.all()
    serializer_class = LeftOverImageSerializer
    update_corners_serializer_class = LeftOverCornersUpdate
    permission_classes = [HasConnection | TokenHasReadWriteScope,
                          ModelPermissions | IsAdminUser | TokenHasReadWriteScope,
                          IsAuthenticated | TokenHasReadWriteScope]
    filterset_class = filters.LeftoverFilter

    @action(methods=['post'], detail=True, )
    def update_corners(self, request: Request, pk=None):
        serializer: LeftOverCornersUpdate = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj: LeftOverImage = self.get_object()
        obj.corners = serializer.validated_data.get('corners')
        obj.save()
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == "update_corners":
            return self.update_corners_serializer_class
        return self.serializer_class


class ErrorFile(GenericAPIView):

    def get(self, request):
        raise FileAccess
