import django_filters

from .models import File


class FileFilter(django_filters.FilterSet):
    modified = django_filters.DateFromToRangeFilter(
        label="Dates",
        widget=django_filters.widgets.RangeWidget(attrs={"type": "date"}),
    )

    class Meta:
        model = File
        fields = ["modified", "private", "parent"]
