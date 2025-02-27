from utilities.filter import OrderingFilterSet
from tags.models import Tag, TagResult


class TagFilterSet(OrderingFilterSet):
    class Meta:
        model = Tag
        fields = dict(
            created=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            modified=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            project=['exact'],
            project_owner=['exact'],
        )


class TagResultFilterSet(OrderingFilterSet):
    class Meta:
        model = TagResult
        fields = dict(
            created=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            modified=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            tag=['exact'],
            tag__project=['exact']
        )
