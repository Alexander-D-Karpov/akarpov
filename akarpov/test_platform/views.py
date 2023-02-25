from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView

from akarpov.test_platform.forms import FormFormClass
from akarpov.test_platform.models import Form
from akarpov.test_platform.services.forms import get_question_types


class FromCreateView(LoginRequiredMixin, CreateView):
    model = Form
    form_class = FormFormClass

    template_name = "test_platform/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = get_question_types()
        return context

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


from_create_view = FromCreateView.as_view()
