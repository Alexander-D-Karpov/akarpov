from django import forms

from akarpov.tools.qr.models import QR


class QRForm(forms.ModelForm):
    body = forms.CharField()

    class Meta:
        model = QR
        fields = ["body"]
