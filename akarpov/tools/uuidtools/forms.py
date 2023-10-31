from django import forms


class UUIDForm(forms.Form):
    token = forms.UUIDField()
