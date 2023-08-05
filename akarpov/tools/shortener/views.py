from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotFound, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from ipware import get_client_ip

from akarpov.tools.shortener.forms import LinkForm
from akarpov.tools.shortener.models import Link
from akarpov.tools.shortener.services import get_cached_link_source, get_link_from_slug
from akarpov.tools.shortener.tasks import save_view_meta


class ShortLinkCreateListView(CreateView, ListView):
    model = Link
    form_class = LinkForm
    paginate_by = 50

    template_name = "tools/shortener/list_create.html"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Link.objects.filter(creator=self.request.user)
        return Link.objects.none()

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.creator = self.request.user
        return super().form_valid(form)


short_link_create_view = ShortLinkCreateListView.as_view()


class LinkDetailView(DetailView):
    template_name = "tools/shortener/view.html"

    def get_object(self, *args, **kwargs):
        link = get_link_from_slug(self.kwargs["slug"])
        if not link:
            raise Http404
        if self.request.user.is_superuser:
            return link
        if link.creator and link.creator != self.request.user:
            raise PermissionDenied
        return link

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["views"] = kwargs["object"].views.all().prefetch_related("user")
        return context


link_detail_view = LinkDetailView.as_view()


class LinkRevokedView(TemplateView):
    template_name = "tools/shortener/revoked.html"


link_revoked_view = LinkRevokedView.as_view()


def redirect_view(request, slug):
    # TODO: move to faster framework, like FastAPI
    link, pk = get_cached_link_source(slug)
    if not link:
        return HttpResponseNotFound("such link doesn't exist or has been revoked")
    ip, is_routable = get_client_ip(request)
    if request.user.is_authenticated:
        user_id = request.user.id
    else:
        user_id = None
    save_view_meta.apply_async(
        kwargs={
            "pk": pk,
            "ip": ip,
            "user_agent": request.META["HTTP_USER_AGENT"],
            "user_id": user_id,
        },
    )
    return HttpResponseRedirect(link)
