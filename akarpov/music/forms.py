from django import forms


class TracksLoadForm(forms.Form):
    address = forms.CharField(max_length=500)


class FileUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}))
