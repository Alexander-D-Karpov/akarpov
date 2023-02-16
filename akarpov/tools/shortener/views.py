from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.views.generic import CreateView, DetailView

from akarpov.tools.shortener.forms import LinkForm
from akarpov.tools.shortener.models import Link
from akarpov.tools.shortener.services import get_link_from_slug


class ShortLinkCreateView(CreateView):
    model = Link
    form_class = LinkForm

    template_name = "shortener/create.html"

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.creator = self.request.user
        return super().form_valid(form)


short_link_create_view = ShortLinkCreateView.as_view()


class LinkDetailView(DetailView):

    template_name = "shortener/view.html"

    def get_object(self, *args, **kwargs):
        link = get_link_from_slug(self.kwargs["slug"])
        if not link:
            raise ObjectDoesNotExist
        if link.creator and link.creator != self.request.user:
            raise PermissionDenied
        return link


link_detail_view = LinkDetailView.as_view()
