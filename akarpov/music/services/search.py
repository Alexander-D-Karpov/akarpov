import re

from django.core.cache import cache
from django.db.models import Case, When
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Q as ES_Q

from akarpov.music.documents import AlbumDocument, AuthorDocument, SongDocument
from akarpov.music.models import Album, Author, Song


def _normalize(text: str) -> str:
    """
    Lowercase and strip punctuation for simple string matching.
    """
    return re.sub(r"\W+", " ", (text or "").lower()).strip()


def _rerank_songs_by_title_and_authors(songs, query, hit_ids):
    norm_query = _normalize(query)
    words = [w for w in norm_query.split() if w]

    split = query.split()
    first_word = re.sub(r"\W+", "", (split[0].lower() if split else ""))

    base_pos = {int(id_): pos for pos, id_ in enumerate(hit_ids)}

    scores = {}

    for song in songs:
        sid = int(song.id)
        name_norm = _normalize(song.name)
        slug_norm = _normalize(getattr(song, "slug", "") or "")
        author_norms = [_normalize(a.name) for a in song.authors.all()]

        score = 0

        if first_word and slug_norm == first_word:
            score += 200
        elif first_word and slug_norm.startswith(first_word):
            score += 150

        name_tokens = name_norm.split()
        if first_word and name_tokens and name_tokens[0] == first_word:
            score += 120
        if first_word and first_word in name_tokens:
            score += 80

        matched_author_words = 0
        for w in words:
            if w in name_tokens:
                score += 10
            for an in author_norms:
                if w in an.split():
                    score += 8
                    matched_author_words += 1

        if matched_author_words >= 2:
            score += 30

        scores[sid] = score

    ordered_ids = sorted(
        [int(i) for i in hit_ids],
        key=lambda sid: (-scores.get(sid, 0), base_pos[sid]),
    )
    return ordered_ids


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
        hit_ids = [int(hit.meta.id) for hit in response.hits]

        song_qs = Song.objects.filter(id__in=hit_ids).prefetch_related("authors")
        songs = list(song_qs)

        if not songs:
            return Song.objects.none()

        ordered_ids = _rerank_songs_by_title_and_authors(songs, query, hit_ids)

        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ordered_ids)])
        return Song.objects.filter(id__in=ordered_ids).order_by(preserved)

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
