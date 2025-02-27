from django_filters.rest_framework import FilterSet
from django_filters import DateRangeFilter, OrderingFilter


class OrderingFilterSet(FilterSet):
    created_at_range = DateRangeFilter(field_name='created')
    ordering = OrderingFilter(
        fields=('created', 'created')
    )
