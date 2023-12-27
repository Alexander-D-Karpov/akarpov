from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from akarpov.files.models import File


@registry.register_document
class FileDocument(Document):
    name = fields.TextField(
        attr="name",
        fields={
            "raw": fields.KeywordField(normalizer="lowercase"),
        },
    )

    description = fields.TextField(
        attr="description",
        fields={
            "raw": fields.KeywordField(normalizer="lowercase"),
        },
    )

    content = fields.TextField(
        attr="content",
        fields={
            "raw": fields.KeywordField(normalizer="lowercase"),
        },
    )

    class Django:
        model = File

    def prepare_description(self, instance):
        return instance.description or ""

    def prepare_content(self, instance):
        # check instance.content is not None
        return (
            instance.content.decode("utf-8")
            if instance.content and isinstance(instance.content, bytes)
            else ""
        )

    class Index:
        name = "files"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}
