from django import forms

from akarpov.files.models import File


class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ["name", "private", "description"]
