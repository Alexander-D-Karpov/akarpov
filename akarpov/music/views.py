from datetime import datetime

import pylast
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from akarpov.common.views import SuperUserRequiredMixin
from akarpov.music.forms import (
    CookieUploadForm,
    DownloadURLForm,
    FileUploadForm,
    TracksLoadForm,
)
from akarpov.music.models import (
    Album,
    Author,
    DownloadJob,
    Playlist,
    Song,
    TempFileUpload,
    UserMusicProfile,
)
from akarpov.music.services.download import (
    CookieManager,
    detect_source,
    is_spotify_rate_limited,
)
from akarpov.music.tasks import (
    process_dir_upload,
    process_download_job,
    process_file_upload,
)


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


playlist_view = PlaylistView.as_view()


class LoadTrackView(SuperUserRequiredMixin, generic.FormView):
    form_class = TracksLoadForm
    template_name = "music/upload.html"

    def get_success_url(self):
        return reverse("music:downloads")

    def form_valid(self, form):
        url = form.data["address"]
        if url.startswith("/"):
            process_dir_upload.apply_async(
                kwargs={"path": url, "user_id": self.request.user.id}
            )
        else:
            job = DownloadJob.objects.create(
                url=url,
                source=detect_source(url),
                creator=self.request.user,
            )
            process_download_job.apply_async(kwargs={"job_id": job.id})
        return super().form_valid(form)


load_track_view = LoadTrackView.as_view()


class LoadTrackFileView(SuperUserRequiredMixin, generic.FormView):
    form_class = FileUploadForm
    template_name = "music/upload.html"

    def get_success_url(self):
        return reverse("music:downloads")

    def form_valid(self, form):
        for file in form.cleaned_data["file"]:
            t = TempFileUpload.objects.create(file=file)
            process_file_upload.apply_async(
                kwargs={"path": t.file.path, "user_id": self.request.user.id}
            )
        return super().form_valid(form)


load_track_file_view = LoadTrackFileView.as_view()


class DownloadsView(SuperUserRequiredMixin, generic.TemplateView):
    template_name = "music/downloads.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["jobs"] = DownloadJob.objects.prefetch_related("tracks").order_by(
            "-created"
        )[:50]
        ctx["url_form"] = DownloadURLForm()
        ctx["file_form"] = FileUploadForm()
        ctx["rate_limited"] = is_spotify_rate_limited()
        ctx["cookies_ok"] = CookieManager.cookies_exist()
        return ctx

    def post(self, request, *args, **kwargs):
        if "file" in request.FILES:
            file_form = FileUploadForm(request.POST, request.FILES)
            if file_form.is_valid():
                for file in file_form.cleaned_data["file"]:
                    t = TempFileUpload.objects.create(file=file)
                    process_file_upload.apply_async(
                        kwargs={"path": t.file.path, "user_id": request.user.id}
                    )
                messages.success(request, "Files queued for processing.")
                return redirect("music:downloads")
        else:
            url_form = DownloadURLForm(request.POST)
            if url_form.is_valid():
                url = url_form.cleaned_data["url"]
                config = url_form.cleaned_data.get("config")
                source = detect_source(url)
                if source == DownloadJob.Source.SPOTIFY and is_spotify_rate_limited():
                    messages.warning(
                        request, "Spotify is rate limited. Job queued for retry."
                    )
                    DownloadJob.objects.create(
                        url=url,
                        source=source,
                        creator=request.user,
                        config=config,
                        status=DownloadJob.Status.RATE_LIMITED,
                        error="Queued -- Spotify rate limited",
                    )
                else:
                    job = DownloadJob.objects.create(
                        url=url,
                        source=source,
                        creator=request.user,
                        config=config,
                    )
                    process_download_job.apply_async(kwargs={"job_id": job.id})
                return redirect("music:downloads")
        return self.get(request, *args, **kwargs)


downloads_view = DownloadsView.as_view()


class CookieManageView(SuperUserRequiredMixin, generic.TemplateView):
    template_name = "music/cookies.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = CookieUploadForm()
        info = CookieManager.get_cookies_info()
        if info:
            ctx["cookie_info"] = info
            ctx["cookie_modified"] = datetime.fromtimestamp(info["modified"])
        ctx["cookies_exist"] = CookieManager.cookies_exist()
        return ctx

    def post(self, request, *args, **kwargs):
        form = CookieUploadForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data["cookies"]
            if not content.strip().startswith(
                "# Netscape HTTP Cookie File"
            ) and not content.strip().startswith("# HTTP Cookie File"):
                messages.error(
                    request, "Invalid cookie file — must start with Netscape header"
                )
            else:
                CookieManager.save_cookies(content)
                messages.success(request, "Cookies saved successfully")
            return redirect("music:cookies")
        return self.get(request, *args, **kwargs)


cookies_view = CookieManageView.as_view()


class MainRadioView(generic.TemplateView):
    template_name = "music/radio.html"


radio_main_view = MainRadioView.as_view()


class MusicPlayerView(generic.TemplateView):
    template_name = "music/player.html"


music_player_view = MusicPlayerView.as_view()


@login_required
def lastfm_auth(request):
    API_KEY = settings.LAST_FM_API_KEY
    if not API_KEY:
        raise Exception("LAST_FM_API_KEY not set")
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
        UserMusicProfile.objects.update_or_create(
            user=request.user,
            defaults={
                "lastfm_token": session_key,
                "lastfm_username": request.user.username,
            },
        )
        messages.success(request, "Last.fm connected")
    except Exception as e:
        messages.error(request, f"Last.fm error: {e}")
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
