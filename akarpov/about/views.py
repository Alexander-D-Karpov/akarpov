from django.views.generic import DetailView, TemplateView

from akarpov.about.models import Project


class AboutView(TemplateView):
    template_name = "about/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = Project.objects.all()
        return context


about_view = AboutView.as_view()


class ProjectView(DetailView):
    model = Project
    slug_field = "pk"
    slug_url_kwarg = "pk"

    template_name = "about/project.html"


project_view = ProjectView.as_view()
