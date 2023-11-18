from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views import generic

from akarpov.common.views import HasPermissions
from akarpov.gallery.forms import ImageUploadForm
from akarpov.gallery.models import Collection, Image, Tag


class ListCollectionsView(generic.ListView):
    model = Collection
    template_name = "gallery/list.html"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.request.user.collections.all()
        return Collection.objects.filter(public=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["collection_previews"] = [
            {
                "collection": collection,
                "preview_images": collection.get_preview_images(),
            }
            for collection in context["collection_list"]
        ]
        return context


list_collections_view = ListCollectionsView.as_view()


class ListTagImagesView(generic.ListView):
    model = Image
    template_name = "gallery/images.html"

    def get_queryset(self):
        tag = get_object_or_404(Tag, slug=self.kwargs["slug"])
        if self.request.user.is_authenticated:
            return Image.objects.filter(tags__contain=tag, user=self.request.user)
        return Image.objects.filter(tags__contain=tag, collection__public=True)


list_tag_images_view = ListTagImagesView.as_view()


class CollectionView(generic.DetailView, HasPermissions):
    model = Collection
    template_name = "gallery/collection.html"


collection_view = CollectionView.as_view()


class ImageView(generic.DetailView, HasPermissions):
    model = Collection
    template_name = "gallery/image.html"


image_view = ImageView.as_view()


class ImageUploadView(LoginRequiredMixin, generic.CreateView):
    model = Image
    form_class = ImageUploadForm
    success_url = ""  # Replace with your success URL

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


image_upload_view = ImageUploadView.as_view()
