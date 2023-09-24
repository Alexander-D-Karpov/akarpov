from django import forms

from akarpov.files.models import File, Folder


class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ["name", "private", "notify_user_on_view", "description"]


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ["name", "private"]
