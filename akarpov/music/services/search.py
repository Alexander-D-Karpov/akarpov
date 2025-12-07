from django.core.cache import cache
from django.db.models import Case, When
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Q as ES_Q

from akarpov.music.documents import AlbumDocument, AuthorDocument, SongDocument
from akarpov.music.models import Album, Author, Song


def search_song(query):
    if not query:
        return Song.objects.none()

    search = SongDocument.search()
    query = query.strip()
    terms = query.split()

    # Phrase matches
    phrase_queries = [
        ES_Q("match_phrase", name={"query": query, "boost": 10}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "match_phrase",
                **{"authors.name": {"query": query, "boost": 9}},
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "match_phrase",
                **{"album.name": {"query": query, "boost": 9}},
            ),
        ),
        ES_Q("match_phrase", name_transliterated={"query": query, "boost": 10}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "match_phrase",
                **{
                    "authors.name_transliterated": {
                        "query": query,
                        "boost": 8,
                    }
                },
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "match_phrase",
                **{
                    "album.name_transliterated": {
                        "query": query,
                        "boost": 8,
                    }
                },
            ),
        ),
    ]

    # Exact keyword matches
    exact_queries = [
        ES_Q("term", **{"name.exact": {"value": query.lower(), "boost": 8}}),
        ES_Q("term", **{"slug.exact": {"value": query.lower(), "boost": 15}}),
    ]

    # Fuzzy matches
    fuzzy_queries = [
        ES_Q("match", name={"query": query, "fuzziness": "AUTO", "boost": 5}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "match",
                **{
                    "authors.name": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": 4,
                    }
                },
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "match",
                **{
                    "album.name": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": 4,
                    }
                },
            ),
        ),
        ES_Q("match", slug={"query": query, "fuzziness": "AUTO", "boost": 5}),
        ES_Q(
            "match",
            name_transliterated={"query": query, "fuzziness": "AUTO", "boost": 4},
        ),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "match",
                **{
                    "authors.name_transliterated": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": 3,
                    }
                },
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "match",
                **{
                    "album.name_transliterated": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": 3,
                    }
                },
            ),
        ),
    ]

    # Wildcard matches
    wildcard_queries = [
        ES_Q("wildcard", name={"value": f"*{query.lower()}*", "boost": 2}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "wildcard",
                **{
                    "authors.name": {
                        "value": f"*{query.lower()}*",
                        "boost": 2,
                    }
                },
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "wildcard",
                **{
                    "album.name": {
                        "value": f"*{query.lower()}*",
                        "boost": 2,
                    }
                },
            ),
        ),
        ES_Q("wildcard", slug={"value": f"*{query.lower()}*", "boost": 2}),
        ES_Q(
            "wildcard",
            name_transliterated={"value": f"*{query.lower()}*", "boost": 2},
        ),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "wildcard",
                **{
                    "authors.name_transliterated": {
                        "value": f"*{query.lower()}*",
                        "boost": 1,
                    }
                },
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "wildcard",
                **{
                    "album.name_transliterated": {
                        "value": f"*{query.lower()}*",
                        "boost": 1,
                    }
                },
            ),
        ),
    ]

    # Optional: extra combined queries if you want them
    combined_queries = []
    if len(terms) >= 2:
        combined_queries.append(
            ES_Q(
                "nested",
                path="authors",
                query=ES_Q(
                    "multi_match",
                    query=query,
                    fields=["authors.name", "authors.name_transliterated"],
                    type="cross_fields",
                    operator="and",
                ),
            )
        )
        combined_queries.append(
            ES_Q(
                "nested",
                path="album",
                query=ES_Q(
                    "multi_match",
                    query=query,
                    fields=["album.name", "album.name_transliterated"],
                    type="cross_fields",
                    operator="and",
                ),
            )
        )

    # Main root-level query (no nested fields here)
    main_query = ES_Q(
        "multi_match",
        query=query,
        fields=[
            "name^5",
            "name_transliterated^4",
            "slug^6",
        ],
        type="best_fields",
        operator="and",
        fuzziness="AUTO",
    )

    should_queries = (
        [main_query]
        + phrase_queries
        + exact_queries
        + fuzzy_queries
        + wildcard_queries
        + combined_queries
    )

    search_query = ES_Q("bool", should=should_queries, minimum_should_match=1)

    response = search.query(search_query).extra(size=20).execute()

    if response.hits:
        hit_ids = [hit.meta.id for hit in response.hits]
        return Song.objects.filter(id__in=hit_ids).order_by(
            Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(hit_ids)])
        )
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
    if not query:
        return Author.objects.none()
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
    if not query:
        return Album.objects.none()
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
