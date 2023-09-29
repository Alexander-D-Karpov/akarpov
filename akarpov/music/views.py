from django.views import generic

from akarpov.common.views import SuperUserRequiredMixin
from akarpov.music.forms import FileUploadForm, TracksLoadForm
from akarpov.music.models import Album, Author, Playlist, Song, TempFileUpload
from akarpov.music.services.base import load_track_file, load_tracks


class AlbumView(generic.DetailView):
    model = Album
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "music/album.html"


album_view = AlbumView.as_view()


class AuthorView(generic.DetailView):
    model = Author
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "music/author.html"


author_view = AuthorView.as_view()


class SongView(generic.DetailView):
    model = Song
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "music/song.html"


song_view = SongView.as_view()


class PlaylistView(generic.DetailView):
    model = Playlist
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "music/playlist.html"


playlist_view = SongView.as_view()


class LoadTrackView(SuperUserRequiredMixin, generic.FormView):
    form_class = TracksLoadForm
    template_name = "music/upload.html"

    def get_success_url(self):
        # TODO: add room to see tracks load
        return ""

    def form_valid(self, form):
        load_tracks(form.data["address"], user_id=self.request.user.id)
        return super().form_valid(form)


load_track_view = LoadTrackView.as_view()


class LoadTrackFileView(SuperUserRequiredMixin, generic.FormView):
    form_class = FileUploadForm
    template_name = "music/upload.html"

    def get_success_url(self):
        # TODO: add room to see tracks load
        return ""

    def form_valid(self, form):
        for file in form.cleaned_data["file"]:
            t = TempFileUpload.objects.create(file=file)
            load_track_file(t.file.path, user_id=self.request.user.id)

        return super().form_valid(form)


load_track_file_view = LoadTrackFileView.as_view()


class MainRadioView(generic.TemplateView):
    template_name = "music/radio.html"


radio_main_view = MainRadioView.as_view()


class MusicPlayerView(generic.ListView):
    template_name = "music/player.html"
    model = Song

    def get_queryset(self):
        return Song.objects.all()


music_player_view = MusicPlayerView.as_view()
