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

    meta = fields.ObjectField(dynamic=True)

    class Index:
        name = "songs"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "filter": {
                    "russian_stop": {
                        "type": "stop",
                        "stopwords": "_russian_",
                    },
                    "russian_keywords": {
                        "type": "keyword_marker",
                        "keywords": ["пример"],
                    },
                    "russian_stemmer": {
                        "type": "stemmer",
                        "language": "russian",
                    },
                    "autocomplete_filter": {
                        "type": "edge_ngram",
                        "min_gram": 1,
                        "max_gram": 20,
                    },
                    "synonym_filter": {
                        "type": "synonym",
                        "synonyms": [
                            "бит,трек,песня,музыка,песня,мелодия,композиция",
                            "певец,исполнитель,артист,музыкант",
                            "альбом,диск,пластинка,сборник,коллекция",
                        ],
                    },
                },
                "analyzer": {
                    "russian": {
                        "tokenizer": "standard",
                        "filter": [
                            "russian_stop",
                            "russian_keywords",
                            "russian_stemmer",
                        ],
                    },
                    "russian_icu": {
                        "tokenizer": "icu_tokenizer",
                        "filter": [
                            "russian_stop",
                            "russian_keywords",
                            "russian_stemmer",
                        ],
                    },
                    "autocomplete": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "autocomplete_filter",
                            "synonym_filter",
                        ],
                    },
                },
            },
        }

    class Django:
        model = Song

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Song):
            return related_instance.album
        return related_instance.songs.all()
