from haystack import indexes

from .models import File


class FileIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name", default="")
    description = indexes.CharField(model_attr="description", default="")
    content = indexes.CharField(model_attr="content", default="")

    def get_model(self):
        return File

    def index_queryset(self, using=None):
        # Return the default queryset to be used for indexing.
        return self.get_model().objects.all()
