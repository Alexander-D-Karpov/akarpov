from django import forms


class PromoCodeForm(forms.Form):
    promocode = forms.CharField(max_length=250, required=True)
