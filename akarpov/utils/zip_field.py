import zipfile

from django import forms

from .validators import validate_zip


class ZipfileField(forms.FileField):
    file_validators = [validate_zip]

    def to_python(self, value):
        value = super().to_python(value)
        for validator in self.file_validators:
            validator(value)
        return zipfile.ZipFile(value)
