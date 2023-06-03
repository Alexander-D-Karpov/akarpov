from django import forms

from akarpov.common.forms import MultipleFileField


class TracksLoadForm(forms.Form):
    address = forms.CharField(max_length=500)


class FileUploadForm(forms.Form):
    file = MultipleFileField()
