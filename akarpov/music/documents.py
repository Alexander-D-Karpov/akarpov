from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from akarpov.music.models import Song


@registry.register_document
class SongDocument(Document):
    authors = fields.NestedField(
        attr="authors",
        properties={
            "name": fields.TextField(
                fields={
                    "raw": fields.KeywordField(normalizer="lowercase"),
                },
            ),
            "link": fields.TextField(),
            "meta": fields.ObjectField(dynamic=True),
        },
    )

    album = fields.NestedField(
        attr="album",
        properties={
            "name": fields.TextField(
                fields={
                    "raw": fields.KeywordField(normalizer="lowercase"),
                },
            ),
            "link": fields.TextField(),
            "meta": fields.ObjectField(dynamic=True),
        },
    )

    name = fields.TextField(
        attr="name",
        fields={
            "raw": fields.KeywordField(normalizer="lowercase"),
        },
    )

    meta = fields.ObjectField(dynamic=True)  # Added meta field here as dynamic object

    class Index:
        name = "songs"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}
        # settings = {
        #     "number_of_shards": 1,
        #     "number_of_replicas": 0,
        #     "analysis": {
        #         "analyzer": {
        #             "russian_icu": {
        #                 "type": "custom",
        #                 "tokenizer": "icu_tokenizer",
        #                 "filter": ["icu_folding","icu_normalizer"]
        #             }
        #         }
        #     }
        # } TODO

    class Django:
        model = Song

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Song):
            return related_instance.album
        return related_instance.songs.all()
