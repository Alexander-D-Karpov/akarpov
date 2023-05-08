from django.views import generic

from akarpov.common.views import HasPermissions
from akarpov.gallery.models import Collection


class ListCollectionsView(generic.ListView):
    model = Collection
    template_name = "gallery/list.html"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.request.user.collections.all()
        return Collection.objects.filter(public=True)


list_collections_view = ListCollectionsView.as_view()


class CollectionView(generic.DetailView, HasPermissions):
    model = Collection
    template_name = "gallery/collection.html"


collection_view = CollectionView.as_view()


class ImageView(generic.DetailView, HasPermissions):
    model = Collection
    template_name = "gallery/image.html"


image_view = ImageView.as_view()