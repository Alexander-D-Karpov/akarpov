from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry

from akarpov.files.models import File


@registry.register_document
class FileDocument(Document):
    class Index:
        name = "files"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = File
        fields = [
            "name",
            "description",
            "content",
        ]

    def prepare_description(self, instance):
        # This method is called for every instance before indexing
        return instance.description or ""

    def prepare_content(self, instance):
        # This method is called for every instance before indexing
        return (
            instance.content.decode("utf-8")
            if isinstance(instance.content, bytes)
            else instance.content
        )
