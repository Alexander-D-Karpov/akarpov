from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from akarpov.music.models import Album, Author, Song


@registry.register_document
class SongDocument(Document):
    authors = fields.NestedField(
        attr="authors",
        properties={
            "name": fields.TextField(
                fields={
                    "raw": fields.KeywordField(normalizer="lowercase_normalizer"),
                },
            ),
            "name_transliterated": fields.TextField(
                analyzer="transliterate",
                fields={
                    "raw": fields.KeywordField(),
                },
            ),
            "link": fields.TextField(),
            "meta": fields.ObjectField(
                dynamic=True,
                properties={
                    "genre": fields.TextField(),
                    "release_year": fields.KeywordField(),
                },
            ),
        },
    )

    album = fields.NestedField(
        attr="album",
        properties={
            "name": fields.TextField(
                fields={
                    "raw": fields.KeywordField(normalizer="lowercase_normalizer"),
                },
            ),
            "name_transliterated": fields.TextField(
                analyzer="transliterate",
                fields={
                    "raw": fields.KeywordField(),
                },
            ),
            "link": fields.TextField(),
            "meta": fields.ObjectField(
                dynamic=True,
                properties={
                    "genre": fields.TextField(),
                    "release_year": fields.KeywordField(),
                },
            ),
        },
    )

    name = fields.TextField(
        attr="name",
        fields={
            "raw": fields.KeywordField(),
            "exact": fields.KeywordField(normalizer="lowercase_normalizer"),
        },
    )
    name_transliterated = fields.TextField(
        attr="name",
        analyzer="transliterate",
        fields={
            "raw": fields.KeywordField(),
        },
    )
    suggest = fields.CompletionField()

    meta = fields.ObjectField(
        dynamic=True,
        properties={
            "genre": fields.TextField(),
            "release_year": fields.KeywordField(),
        },
    )

    class Index:
        name = "songs"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "normalizer": {
                    "lowercase_normalizer": {
                        "type": "custom",
                        "char_filter": [],
                        "filter": ["lowercase"],
                    }
                },
                "filter": {
                    "my_transliterator": {
                        "type": "icu_transform",
                        "id": "Any-Latin; NFD; [:Nonspacing Mark:] Remove; NFC",
                    },
                    "russian_stop": {
                        "type": "stop",
                        "stopwords": "_russian_",
                    },
                    "russian_keywords": {
                        "type": "keyword_marker",
                        "keywords": ["песня", "музыка", "певец", "альбом"],
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
                    "transliterate": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "my_transliterator",
                        ],
                    },
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
                            "english_stemmer",
                            "russian_stemmer",
                        ],
                    },
                    "search_synonym_with_stemming": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "synonym_filter",
                            "english_stemmer",
                            "russian_stemmer",
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


@registry.register_document
class AuthorDocument(Document):
    name = fields.TextField(
        fields={
            "raw": fields.KeywordField(),
            "exact": fields.KeywordField(normalizer="lowercase_normalizer"),
        },
    )
    name_transliterated = fields.TextField(
        attr="name",
        analyzer="transliterate",
        fields={
            "raw": fields.KeywordField(),
        },
    )
    suggest = fields.CompletionField()
    meta = fields.ObjectField(
        dynamic=True,
        properties={
            "description": fields.TextField(),
            # Ensure no empty date fields here either
            "popularity": fields.IntegerField(),
        },
    )

    class Index:
        name = "authors"
        settings = SongDocument.Index.settings

    class Django:
        model = Author


@registry.register_document
class AlbumDocument(Document):
    name = fields.TextField(
        fields={
            "raw": fields.KeywordField(),
            "exact": fields.KeywordField(normalizer="lowercase_normalizer"),
        },
    )
    name_transliterated = fields.TextField(
        attr="name",
        analyzer="transliterate",
        fields={
            "raw": fields.KeywordField(),
        },
    )
    suggest = fields.CompletionField()
    meta = fields.ObjectField(
        dynamic=True,
        properties={
            "genre": fields.TextField(),
            "release_year": fields.KeywordField(),
        },
    )
    authors = fields.NestedField(
        attr="authors",
        properties={
            "name": fields.TextField(
                fields={
                    "raw": fields.KeywordField(normalizer="lowercase"),
                },
            ),
            "name_transliterated": fields.TextField(
                analyzer="transliterate",
                fields={
                    "raw": fields.KeywordField(),
                },
            ),
            "link": fields.TextField(),
            "meta": fields.ObjectField(dynamic=True),
        },
    )

    class Index:
        name = "albums"
        settings = SongDocument.Index.settings

    class Django:
        model = Album
