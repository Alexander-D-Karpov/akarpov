import json

from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.forms import DateInput, TextInput
from django.utils.translation import gettext_lazy as _

from akarpov.users.models import UserAPIToken

User = get_user_model()


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User


class UserAdminCreationForm(admin_forms.UserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User

        error_messages = {
            "username": {"unique": _("This username has already been taken.")}
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """


class OTPForm(forms.Form):
    otp_token = forms.CharField()


class TokenCreationForm(forms.ModelForm):
    permissions = forms.MultipleChoiceField(
        choices=[],  # To be set in __init__
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = UserAPIToken
        fields = ["name", "active_until", "permissions"]
        widgets = {
            "name": TextInput(attrs={"placeholder": "Token Name (Optional)"}),
            "active_until": DateInput(attrs={"type": "date"}, format="%d.%m.%Y"),
        }
        # Make active_until not required
        required = {
            "active_until": False,
        }

    def __init__(self, *args, **kwargs):
        permissions_context = kwargs.pop("permissions_context", None)
        super().__init__(*args, **kwargs)

        if permissions_context:
            for app, actions in permissions_context.items():
                field_name = f"permissions_{app}"
                self.fields[field_name] = forms.MultipleChoiceField(
                    choices=[(action, action) for action in actions.keys()],
                    widget=forms.CheckboxSelectMultiple,
                    required=False,
                    label=app.capitalize(),
                    initial=[
                        item
                        for sublist in kwargs.get("initial", {}).get(field_name, [])
                        for item in sublist
                    ],
                )
        self.fields["active_until"].required = False

    def get_permissions_choices(self):
        permissions_choices = [
            (f"{app}.{action}", description)
            for app, actions in UserAPIToken.permission_template.items()
            for action, description in actions.items()
        ]
        return permissions_choices

    def clean(self):
        cleaned_data = super().clean()
        structured_permissions = {
            category: {perm: False for perm in permissions.keys()}
            for category, permissions in UserAPIToken.permission_template.items()
        }

        for category in structured_permissions.keys():
            input_field_name = f"permissions_{category}"
            if input_field_name in self.data:
                selected_perms = self.data.getlist(input_field_name)
                for perm in selected_perms:
                    if perm in structured_permissions[category]:
                        structured_permissions[category][perm] = True

        cleaned_data["permissions"] = json.dumps(structured_permissions)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        permissions_json = self.cleaned_data.get("permissions", "{}")
        instance.permissions = json.loads(permissions_json)

        if commit:
            instance.save()

        return instance
