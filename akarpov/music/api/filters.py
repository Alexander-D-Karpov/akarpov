from django_filters import rest_framework as filters

from akarpov.music.models import Playlist


class PlaylistFilter(filters.FilterSet):
    class Meta:
        model = Playlist
        fields = ()
