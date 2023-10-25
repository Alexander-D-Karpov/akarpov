from django import forms

from akarpov.users.themes.models import Theme


class ThemeForm(forms.ModelForm):
    class Meta:
        model = Theme
        fields = ["name", "file", "color"]
