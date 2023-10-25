from django.views import generic

from akarpov.common.views import SuperUserRequiredMixin
from akarpov.users.themes.models import Theme


class CreateFormView(generic.CreateView, SuperUserRequiredMixin):
    model = Theme
    fields = ["name", "file", "color"]
    template_name = "users/themes/create.html"

    def get_success_url(self):
        return ""
