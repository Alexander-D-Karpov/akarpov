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
                    "english_stemmer": {
                        "type": "stemmer",
                        "language": "english",
                    },
                    "autocomplete_filter": {
                        "type": "edge_ngram",
                        "min_gram": 1,
                        "max_gram": 20,
                    },
                    "synonym_filter": {
                        "type": "synonym",
                        "synonyms": [
                            "бит, трек => песня",
                            "песня, музыка, мелодия, композиция",
                            "певец, исполнитель, артист, музыкант",
                            "альбом, диск, пластинка, сборник, коллекция",
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
                    "russian_with_synonyms_and_stemming": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "russian_stop",
                            "russian_keywords",
                            "russian_stemmer",
                            "synonym_filter",
                        ],
                    },
                    "english_with_stemming": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "english_stemmer",
                        ],
                    },
                    "autocomplete_with_stemming": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "autocomplete_filter",
                            "english_stemmer",  # Apply English stemming for autocomplete
                            "russian_stemmer",  # Include Russian stemming if applicable
                        ],
                    },
                    "search_synonym_with_stemming": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "synonym_filter",
                            "english_stemmer",  # Apply English stemming for synonym search
                            "russian_stemmer",  # Include Russian stemming if processing Russian synonyms
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
