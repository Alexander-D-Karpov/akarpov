import pylast
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from akarpov.common.views import SuperUserRequiredMixin
from akarpov.music.forms import FileUploadForm, TracksLoadForm
from akarpov.music.models import (
    Album,
    Author,
    Playlist,
    Song,
    TempFileUpload,
    UserMusicProfile,
)
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


@login_required
def lastfm_auth(request):
    API_KEY = settings.LAST_FM_API_KEY

    if not API_KEY:
        raise Exception("LAST_FM_API_KEY not set in settings")

    callback_url = (
        f"https://{get_current_site(request).domain}{reverse('music:lastfm_callback')}"
    )
    auth_url = f"http://www.last.fm/api/auth/?api_key={API_KEY}&cb={callback_url}"

    return redirect(auth_url)


@login_required
def lastfm_callback(request):
    API_KEY = settings.LAST_FM_API_KEY
    API_SECRET = settings.LAST_FM_SECRET

    token = request.GET.get("token")
    if not token:
        messages.error(request, "No token provided by Last.fm")
        return redirect(reverse("music:landing"))

    network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
    skg = pylast.SessionKeyGenerator(network)

    try:
        session_key = skg.get_web_auth_session_key(url="", token=token)

        user = request.user
        UserMusicProfile.objects.update_or_create(
            user=user,
            defaults={
                "lastfm_token": session_key,
                "lastfm_username": user.username,
            },
        )
        messages.success(request, "Last.fm account is successfully connected")
    except Exception as e:
        messages.error(
            request, f"There was an error connecting your Last.fm account: {e}"
        )

    return redirect(reverse("music:landing"))


class MusicLanding(generic.TemplateView):
    template_name = "music/landing.html"

    def get_context_data(self, **kwargs):
        if self.request.user.is_authenticated:
            try:
                kwargs["last_fm_account"] = UserMusicProfile.objects.get(
                    user=self.request.user
                ).lastfm_username
            except UserMusicProfile.DoesNotExist:
                kwargs["last_fm_account"] = None
        return super().get_context_data(**kwargs)


music_landing = MusicLanding.as_view()
