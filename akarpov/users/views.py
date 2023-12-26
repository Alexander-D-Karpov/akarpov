from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from akarpov.users.models import UserHistory
from akarpov.users.services.history import create_history_warning_note
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
