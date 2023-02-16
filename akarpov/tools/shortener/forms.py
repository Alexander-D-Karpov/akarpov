from django import forms
from django.core.validators import URLValidator

from akarpov.tools.shortener.models import Link


class LinkForm(forms.ModelForm):
    source = forms.URLField(
        max_length=500,
        widget=forms.TextInput,
        help_text="Please enter the url of the page",
        validators=[URLValidator],
    )

    class Meta:
        model = Link
        fields = ["source"]
