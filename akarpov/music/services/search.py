from django.core.cache import cache
from django.db.models import Case, When
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Q as ES_Q

from akarpov.music.documents import AlbumDocument, AuthorDocument, SongDocument
from akarpov.music.models import Album, Author, Song


def search_song(query):
    search = SongDocument.search()

    # Split the query into words
    terms = query.strip().split()

    # Initialize must and should clauses
    must_clauses = []
    should_clauses = []

    # Build queries for song names
    song_name_queries = [
        ES_Q("match_phrase", name={"query": query, "boost": 5}),
        ES_Q("match", name={"query": query, "fuzziness": "AUTO", "boost": 4}),
        ES_Q("wildcard", name={"value": f"*{query.lower()}*", "boost": 2}),
    ]

    # Build queries for author names
    author_name_queries = [
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q("match_phrase", name={"query": query, "boost": 5}),
        ),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q("match", name={"query": query, "fuzziness": "AUTO", "boost": 4}),
        ),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q("wildcard", name={"value": f"*{query.lower()}*", "boost": 2}),
        ),
    ]

    # If the query contains multiple terms, assume it might include both song and author names
    if len(terms) > 1:
        # Build combined queries
        must_clauses.extend(
            [
                ES_Q("bool", should=song_name_queries),
                ES_Q("bool", should=author_name_queries),
            ]
        )
    else:
        # If single term, search both song and author names but with lower boost
        should_clauses.extend(song_name_queries + author_name_queries)

    # Combine must and should clauses
    if must_clauses:
        search_query = ES_Q("bool", must=must_clauses, should=should_clauses)
    else:
        search_query = ES_Q("bool", should=should_clauses, minimum_should_match=1)

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
