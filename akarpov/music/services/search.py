from django.core.cache import cache
from django.db.models import Case, When
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Q as ES_Q

from akarpov.music.documents import AlbumDocument, AuthorDocument, SongDocument
from akarpov.music.models import Album, Author, Song


def search_song(query):
    # Split query into potential track and artist parts
    parts = [part.strip() for part in query.split("-")]
    track_query = parts[0]
    artist_query = parts[1] if len(parts) > 1 else None

    search = SongDocument.search()

    # Base queries for track name with high boost
    should_queries = [
        ES_Q("match_phrase", name={"query": track_query, "boost": 10}),
        ES_Q("match", name={"query": track_query, "fuzziness": "AUTO", "boost": 8}),
        ES_Q("wildcard", name={"value": f"*{track_query.lower()}*", "boost": 6}),
        ES_Q(
            "match",
            name_transliterated={"query": track_query, "fuzziness": "AUTO", "boost": 5},
        ),
    ]

    # Add artist-specific queries if artist part exists
    if artist_query:
        should_queries.extend(
            [
                ES_Q(
                    "nested",
                    path="authors",
                    query=ES_Q(
                        "match_phrase", name={"query": artist_query, "boost": 4}
                    ),
                ),
                ES_Q(
                    "nested",
                    path="authors",
                    query=ES_Q(
                        "match",
                        name={"query": artist_query, "fuzziness": "AUTO", "boost": 3},
                    ),
                ),
                ES_Q(
                    "nested",
                    path="authors",
                    query=ES_Q(
                        "wildcard",
                        name={"value": f"*{artist_query.lower()}*", "boost": 2},
                    ),
                ),
            ]
        )
    else:
        # If no explicit artist, still search in authors but with lower boost
        should_queries.extend(
            [
                ES_Q(
                    "nested",
                    path="authors",
                    query=ES_Q("match_phrase", name={"query": track_query, "boost": 2}),
                ),
                ES_Q(
                    "nested",
                    path="authors",
                    query=ES_Q(
                        "match",
                        name={"query": track_query, "fuzziness": "AUTO", "boost": 1},
                    ),
                ),
            ]
        )

    # Add album queries with lower boost
    should_queries.extend(
        [
            ES_Q(
                "nested",
                path="album",
                query=ES_Q("match_phrase", name={"query": track_query, "boost": 1.5}),
            ),
            ES_Q(
                "nested",
                path="album",
                query=ES_Q(
                    "match",
                    name={"query": track_query, "fuzziness": "AUTO", "boost": 1},
                ),
            ),
        ]
    )

    # Combine all queries with minimum_should_match=1
    search_query = ES_Q("bool", should=should_queries, minimum_should_match=1)

    # Execute search with size limit
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
