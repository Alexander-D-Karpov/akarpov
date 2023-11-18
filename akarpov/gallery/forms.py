from django import forms

from akarpov.gallery.models import Collection, Image


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = (
            "collection",
            "public",
        )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["collection"].queryset = Collection.objects.filter(user=user)


ImageFormSet = forms.modelformset_factory(
    Image,
    form=ImageUploadForm,
    extra=3,  # Number of images to upload at once; adjust as needed
)
