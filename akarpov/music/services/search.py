from django.core.cache import cache
from django.db.models import Case, When
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Q as ES_Q

from akarpov.music.documents import AlbumDocument, AuthorDocument, SongDocument
from akarpov.music.models import Album, Author, Song


def search_song(query):
    search = SongDocument.search()

    should_queries = [
        ES_Q("match_phrase", name={"query": query, "boost": 5}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q("match_phrase", name={"query": query, "boost": 4}),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q("match_phrase", name={"query": query, "boost": 4}),
        ),
        ES_Q("match", name={"query": query, "fuzziness": "AUTO", "boost": 3}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q("match", name={"query": query, "fuzziness": "AUTO", "boost": 2}),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q("match", name={"query": query, "fuzziness": "AUTO", "boost": 2}),
        ),
        ES_Q("wildcard", name={"value": f"*{query.lower()}*", "boost": 1}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q("wildcard", name={"value": f"*{query.lower()}*", "boost": 0.8}),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q("wildcard", name={"value": f"*{query.lower()}*", "boost": 0.8}),
        ),
        ES_Q(
            "match",
            name_transliterated={"query": query, "fuzziness": "AUTO", "boost": 1},
        ),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "match",
                name_transliterated={"query": query, "fuzziness": "AUTO", "boost": 0.8},
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "match",
                name_transliterated={"query": query, "fuzziness": "AUTO", "boost": 0.8},
            ),
        ),
    ]

    search_query = ES_Q("bool", should=should_queries, minimum_should_match=1)

    search = search.query(search_query).extra(size=20)
    response = search.execute()

    if response.hits:
        hit_ids = [hit.meta.id for hit in response.hits]
        songs = Song.objects.filter(id__in=hit_ids).order_by(
            Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(hit_ids)])
        )
        return songs

    return Song.objects.none()


def autocomplete_search(query):
    s = SongDocument.search()
    s = s.suggest("song_suggest", query, completion={"field": "suggest"})
    suggestions = s.execute().suggest.song_suggest[0].options
    return [option.text for option in suggestions]


def get_popular_songs():
    if "popular_songs" in cache:
        return cache.get("popular_songs")
    else:
        songs = Song.objects.filter(played__gt=300).order_by("-played")[:10]
        cache.set("popular_songs", songs, timeout=3600)
        return songs


def bulk_update_index(model_class):
    qs = model_class.objects.all()
    registry.update(qs, bulk_size=100)


def search_author(query):
    search = AuthorDocument.search()

    should_queries = [
        ES_Q("match_phrase", name={"query": query, "boost": 5}),
        ES_Q("match", name={"query": query, "fuzziness": "AUTO", "boost": 3}),
        ES_Q("wildcard", name={"value": f"*{query.lower()}*", "boost": 1}),
        ES_Q(
            "match",
            name_transliterated={"query": query, "fuzziness": "AUTO", "boost": 1},
        ),
    ]

    search_query = ES_Q("bool", should=should_queries, minimum_should_match=1)
    search = search.query(search_query).extra(size=10)
    response = search.execute()

    if response.hits:
        hit_ids = [hit.meta.id for hit in response.hits]
        authors = Author.objects.filter(id__in=hit_ids).order_by(
            Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(hit_ids)])
        )
        return authors

    return Author.objects.none()


def search_album(query):
    search = AlbumDocument.search()

    should_queries = [
        ES_Q("match_phrase", name={"query": query, "boost": 5}),
        ES_Q("match", name={"query": query, "fuzziness": "AUTO", "boost": 3}),
        ES_Q("wildcard", name={"value": f"*{query.lower()}*", "boost": 1}),
        ES_Q(
            "match",
            name_transliterated={"query": query, "fuzziness": "AUTO", "boost": 1},
        ),
    ]

    search_query = ES_Q("bool", should=should_queries, minimum_should_match=1)
    search = search.query(search_query).extra(size=10)
    response = search.execute()

    if response.hits:
        hit_ids = [hit.meta.id for hit in response.hits]
        albums = Album.objects.filter(id__in=hit_ids).order_by(
            Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(hit_ids)])
        )
        return albums

    return Album.objects.none()
