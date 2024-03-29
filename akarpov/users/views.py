from allauth.account.views import LoginView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, RedirectView, UpdateView
from django_otp import user_has_device
from django_otp.plugins.otp_totp.models import TOTPDevice

from akarpov.users.forms import OTPForm, TokenCreationForm
from akarpov.users.models import UserAPIToken, UserHistory
from akarpov.users.services.history import create_history_warning_note
from akarpov.users.services.two_factor import generate_qr_code
from akarpov.users.themes.models import Theme

User = get_user_model()


class UserDetailView(DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["username", "name", "image", "about", "agree_data_to_be_sold"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        return self.request.user.get_absolute_url()

    def get_context_data(self, **kwargs):
        kwargs["themes"] = Theme.objects.all()
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        data = self.request.POST
        if "theme" in data:
            if data["theme"] == "0":
                self.object.theme = None
            else:
                try:
                    self.object.theme = Theme.objects.get(id=data["theme"])
                except Theme.DoesNotExist:
                    ...
        return super().form_valid(form)

    def get_object(self):
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()


class UserHistoryListView(LoginRequiredMixin, ListView):
    model = UserHistory
    template_name = "users/history.html"

    def get_queryset(self):
        return UserHistory.objects.filter(user=self.request.user)


user_history_view = UserHistoryListView.as_view()


class UserHistoryDeleteView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self):
        q = UserHistory.objects.filter(user=self.request.user).exclude(
            type=UserHistory.RecordType.warning
        )
        if q:
            q.delete()
            create_history_warning_note(
                self.request.user, "History", "Deleted history", self.request.user
            )
        return reverse("users:history")


user_history_delete_view = UserHistoryDeleteView.as_view()


@login_required
def enable_2fa_view(request):
    user = request.user
    devices = TOTPDevice.objects.filter(user=user, confirmed=True)
    qr_code_svg = None
    totp_key = None

    if devices.exists():
        if request.method == "POST":
            form = OTPForm(request.POST)
            if form.is_valid():
                token = form.cleaned_data["otp_token"]

                # Verifying the token against all confirmed devices
                for device in devices:
                    if device.verify_token(token):
                        device.delete()  # Delete the device if the token is valid

                # Check if there are still confirmed devices left
                if not TOTPDevice.objects.filter(user=user, confirmed=True).exists():
                    messages.success(request, "Two-factor authentication disabled!")
                    return redirect(reverse_lazy("blog:post_list"))
                else:
                    messages.error(request, "Invalid token, please try again.")
            else:
                messages.error(
                    request, "The form submission was not valid. Please, try again."
                )
        form = OTPForm(initial={"otp_token": ""})
        return render(request, "users/disable_2fa.html", {"form": form})

    else:
        if request.method == "POST":
            device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
            if request.POST.get("cancel"):
                device.delete()
                return redirect(reverse_lazy("blog:post_list"))
            form = OTPForm(request.POST)
            if form.is_valid():
                token = form.cleaned_data["otp_token"]
                if device and device.verify_token(token):
                    device.confirmed = True
                    device.save()
                    messages.success(request, "Two-factor authentication enabled!")
                    return redirect(reverse_lazy("blog:post_list"))
                else:
                    messages.error(request, "Invalid token, please try again.")
        else:
            device, created = TOTPDevice.objects.get_or_create(
                user=user, confirmed=False
            )
            site_name = get_current_site(request).name
            provisioning_url = device.config_url
            provisioning_url_site = provisioning_url.replace(
                "otpauth://totp/", f"otpauth://totp/{site_name}:"
            )
            qr_code_svg = generate_qr_code(provisioning_url_site)
            totp_key = device.key  # get device's secret key

            form = OTPForm(initial={"otp_token": ""})

        return render(
            request,
            "users/enable_2fa.html",
            {"form": form, "qr_code_svg": qr_code_svg, "totp_key": totp_key},
        )


class OTPLoginView(LoginView):
    def form_valid(self, form):
        # Store URL for next page from the Login form
        self.request.session["next"] = self.request.GET.get("next")

        resp = super().form_valid(form)

        # Redirect users with OTP devices to enter their tokens
        if user_has_device(self.request.user):
            return HttpResponseRedirect(reverse("users:enforce_otp_login"))

        return resp


login_view = OTPLoginView.as_view()


@login_required
def enforce_otp_login(request):
    next_url = request.GET.get("next")

    if not next_url:
        next_url = request.session.get("next", reverse_lazy("home"))

    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_token = form.cleaned_data["otp_token"]
            device = TOTPDevice.objects.filter(user=request.user).first()
            if device.verify_token(otp_token):
                request.session["otp_verified"] = True
                request.session.pop("next", None)
                return redirect(next_url)
    else:
        form = OTPForm()
    return render(request, "users/otp_verify.html", {"form": form})


@login_required
def list_tokens(request):
    tokens = UserAPIToken.objects.filter(user=request.user).order_by("-last_used")
    return render(request, "users/list_tokens.html", {"tokens": tokens})


@login_required
def create_token(request):
    initial_data = {}

    # Обработка параметров 'name' и 'active_until'
    if "name" in request.GET:
        initial_data["name"] = request.GET["name"]
    if "active_until" in request.GET:
        initial_data["active_until"] = request.GET["active_until"]

    # Создаем QueryDict для разрешений, чтобы правильно обработать повторяющиеся ключи
    permissions_query_dict = QueryDict("", mutable=True)

    # Разбор параметров разрешений
    permissions = request.GET.getlist("permissions")
    for perm in permissions:
        category, permission = perm.split(".")
        permissions_query_dict.update({f"permissions_{category}": [permission]})

    # Переводим QueryDict в обычный словарь для использования в initial
    permissions_data = {key: value for key, value in permissions_query_dict.lists()}

    initial_data.update(permissions_data)

    for key, value_list in permissions_data.items():
        initial_data[key] = [item for sublist in value_list for item in sublist]

    form = TokenCreationForm(
        initial=initial_data, permissions_context=UserAPIToken.permission_template
    )
    if request.method == "POST":
        print(request.POST)
        form = TokenCreationForm(request.POST)
        if form.is_valid():
            new_token = form.save(commit=False)
            new_token.user = request.user
            new_token.token = UserAPIToken.generate_token()
            new_token.save()
            token_created = new_token.token
            return render(
                request, "users/token_created.html", {"new_token": token_created}
            )

    return render(request, "users/create_token.html", {"form": form})


@login_required
def view_token(request, token_id):
    token = get_object_or_404(UserAPIToken, id=token_id, user=request.user)
    return render(request, "users/view_token.html", {"token": token})


@login_required
def delete_token(request, token_id):
    token = get_object_or_404(UserAPIToken, id=token_id, user=request.user)
    if request.method == "POST":
        token.delete()
        return redirect("users:list_tokens")
    return render(request, "users/confirm_delete_token.html", {"token": token})
