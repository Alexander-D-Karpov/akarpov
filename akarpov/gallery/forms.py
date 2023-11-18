from django import forms

from akarpov.common.forms import MultipleFileField
from akarpov.gallery.models import Collection, Image


class ImageUploadForm(forms.ModelForm):
    image = MultipleFileField

    class Meta:
        model = Image
        fields = (
            "image",
            "collection",
            "public",
        )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["collection"].queryset = Collection.objects.filter(user=user)

    def save(self, commit=True):
        files = self.files.getlist("image")
        instances = []
        for file in files:
            instance = self.instance
            instance.image = file
            if commit:
                instance.save()
            instances.append(instance)
        return instances


ImageFormSet = forms.modelformset_factory(
    Image,
    form=ImageUploadForm,
    extra=3,  # Number of images to upload at once; adjust as needed
)
