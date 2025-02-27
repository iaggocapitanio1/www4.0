from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework import mixins
from tags.models import Tag, TagResult
from tags.serializers import TagSerializer, TagResultSerializer
from tags.filters import TagFilterSet, TagResultFilterSet


class TagsViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filterset_class = TagFilterSet


class TagsResultViewSet(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    queryset = TagResult.objects.all()
    serializer_class = TagResultSerializer
    filterset_class = TagResultFilterSet
