import django_filters

from bucket.models import File, Folder, LeftOverImage
from utilities.filter import OrderingFilterSet


class FileFilterSet(OrderingFilterSet):
    path = django_filters.CharFilter(method='filter_by_folder', label="Filter by Folder Path")

    class Meta:
        model = File
        fields = dict(
            created=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            modified=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            file_type=['exact'],
            folder=['exact'],
        )

    @staticmethod
    def filter_by_folder(queryset, name, value):
        folders = Folder.objects.filter(path__icontains=value)
        return queryset.filter(folder__in=folders)


class FolderFilterSet(OrderingFilterSet):
    class Meta:
        model = Folder
        fields = dict(
            created=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            modified=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            name=['exact'],
            user=['exact'],
            budget=['exact'],
            path=['exact'],
            parent=['exact']
        )


class LeftoverFilter(OrderingFilterSet):
    class Meta:
        model = LeftOverImage
        fields = dict(
            created=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            modified=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            treated=['exact'],
            confirmed=['exact'],
            klass=['exact', 'icontains'])
