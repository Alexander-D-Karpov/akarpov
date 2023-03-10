from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView, DetailView

from akarpov.test_platform.forms import FormFormClass
from akarpov.test_platform.models import BaseQuestion, Form
from akarpov.test_platform.services.forms import get_question_types, parse_form_create
from akarpov.test_platform.services.generators import generate_form_question


class FromCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Form
    form_class = FormFormClass

    template_name = "test_platform/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = get_question_types()
        return context

    def form_valid(self, form):
        form.instance.creator = self.request.user
        s = super().form_valid(form)
        fields = parse_form_create(self.request.POST)
        for i, field in enumerate(fields):
            question: BaseQuestion = field["type"]
            field.pop("type")
            question.objects.create(**field, order=i, form_id=form.instance.id)
        return s


form_create_view = FromCreateView.as_view()


class FormView(DetailView):
    template_name = "test_platform/view.html"
    model = Form
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = generate_form_question(self.object)
        return context


form_view = FormView.as_view()
