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

    # Priorities:
    # 1. Combined field matches (Song name + Author/Album) – highest priority
    # 2. Exact phrase matches in name, author name, album name
    # 3. Exact keyword matches (name.exact, slug.exact)
    # 4. Fuzzy matches (name, authors, album, slug, including transliterated fields)
    # 5. Wildcard matches (name, authors, album, slug, including transliterated fields)

    # Phrase matches (high priority for exact phrases in each field)
    phrase_queries = [
        ES_Q("match_phrase", name={"query": query, "boost": 10}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "match_phrase", **{"authors__name": {"query": query, "boost": 9}}
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q("match_phrase", **{"album__name": {"query": query, "boost": 9}}),
        ),
        # Include transliterated name and names for phrase matching
        ES_Q("match_phrase", name_transliterated={"query": query, "boost": 10}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "match_phrase",
                **{"authors__name_transliterated": {"query": query, "boost": 8}},
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "match_phrase",
                **{"album__name_transliterated": {"query": query, "boost": 8}},
            ),
        ),
    ]

    # Exact keyword matches (case-insensitive exact matches)
    exact_queries = [
        ES_Q("term", **{"name.exact": {"value": query.lower(), "boost": 8}}),
        ES_Q(
            "term", **{"slug.exact": {"value": query.lower(), "boost": 15}}
        ),  # exact slug match (highest boost)
    ]

    # Fuzzy matches (to catch typos or variations)
    fuzzy_queries = [
        ES_Q("match", name={"query": query, "fuzziness": "AUTO", "boost": 5}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "match",
                **{"authors__name": {"query": query, "fuzziness": "AUTO", "boost": 4}},
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "match",
                **{"album__name": {"query": query, "fuzziness": "AUTO", "boost": 4}},
            ),
        ),
        ES_Q(
            "match", slug={"query": query, "fuzziness": "AUTO", "boost": 5}
        ),  # fuzzy on slug
        # Fuzzy on transliterated fields
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
                    "authors__name_transliterated": {
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
                    "album__name_transliterated": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": 3,
                    }
                },
            ),
        ),
    ]

    # Wildcard matches (partial substrings)
    wildcard_queries = [
        ES_Q("wildcard", name={"value": f"*{query.lower()}*", "boost": 2}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "wildcard",
                **{"authors__name": {"value": f"*{query.lower()}*", "boost": 2}},
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "wildcard",
                **{"album__name": {"value": f"*{query.lower()}*", "boost": 2}},
            ),
        ),
        ES_Q("wildcard", slug={"value": f"*{query.lower()}*", "boost": 2}),
        # Wildcard on transliterated fields
        ES_Q(
            "wildcard", name_transliterated={"value": f"*{query.lower()}*", "boost": 2}
        ),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "wildcard",
                **{
                    "authors__name_transliterated": {
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
                    "album__name_transliterated": {
                        "value": f"*{query.lower()}*",
                        "boost": 1,
                    }
                },
            ),
        ),
    ]

    # Combined field matches (song name + author/album terms) for multi-term queries
    combined_queries = []
    if len(terms) >= 2:
        # If query has multiple words, require all terms across name and author fields (song title + author)
        combined_queries.append(
            ES_Q(
                "multi_match",
                query=query,
                fields=["name", "authors.name"],
                type="cross_fields",
                operator="and",
                boost=12,
            )
        )
        # Song title + album combination
        combined_queries.append(
            ES_Q(
                "multi_match",
                query=query,
                fields=["name", "album.name"],
                type="cross_fields",
                operator="and",
                boost=11,
            )
        )
    if len(terms) >= 3:
        # If query has three or more terms, consider title+author+album all present
        combined_queries.append(
            ES_Q(
                "multi_match",
                query=query,
                fields=["name", "authors.name", "album.name"],
                type="cross_fields",
                operator="and",
                boost=13,
            )
        )

    # Combine all queries using SHOULD (OR), so any can match, with boosts determining relevance
    should_queries = (
        phrase_queries
        + exact_queries
        + fuzzy_queries
        + wildcard_queries
        + combined_queries
    )
    search_query = ES_Q("bool", should=should_queries, minimum_should_match=1)

    # Execute search with a reasonable limit
    response = search.query(search_query).extra(size=20).execute()

    if response.hits:
        # Preserve the search result ordering
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
