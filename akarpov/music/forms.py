from django import forms

from akarpov.common.forms import MultipleFileField
from akarpov.music.models import DownloadConfig


class TracksLoadForm(forms.Form):
    address = forms.CharField(max_length=500)


class FileUploadForm(forms.Form):
    file = MultipleFileField()


class CookieUploadForm(forms.Form):
    cookies = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 15,
                "class": "form-control font-monospace",
                "placeholder": "Paste Netscape cookie file content here...",
            }
        ),
    )


class DownloadURLForm(forms.Form):
    url = forms.CharField(
        max_length=500,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Spotify / YouTube / SoundCloud URL",
            }
        ),
    )
    config = forms.ModelChoiceField(
        queryset=DownloadConfig.objects.all(),
        required=False,
        empty_label="Default config (from settings)",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
