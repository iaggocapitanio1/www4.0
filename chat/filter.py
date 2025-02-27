from utilities.filter import OrderingFilterSet
from chat.models import Message


class MessageFilterSet(OrderingFilterSet):
    class Meta:
        model = Message
        fields = dict(
            created=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            modified=['gt', 'lt', 'week__gt', 'week__lt', 'year__gt', 'year__lt', 'day__lt', 'day__gt'],
            project=['exact']

        )
