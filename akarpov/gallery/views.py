from django.shortcuts import get_object_or_404
from django.views import generic

from akarpov.common.views import HasPermissions
from akarpov.gallery.models import Collection, Image, Tag


class ListCollectionsView(generic.ListView):
    model = Collection
    template_name = "gallery/list.html"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.request.user.collections.all()
        return Collection.objects.filter(public=True)


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
