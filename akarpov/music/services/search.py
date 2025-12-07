import re

from django.core.cache import cache
from django.db.models import Case, When
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Q as ES_Q

from akarpov.music.documents import AlbumDocument, AuthorDocument, SongDocument
from akarpov.music.models import Album, Author, Song

_WORD_RE = re.compile(r"\w+", re.U)


def _normalize(text: str) -> str:
    if not text:
        return ""
    return text.lower().strip()


def _tokenize(text: str):
    if not text:
        return []
    return _WORD_RE.findall(_normalize(text))


def _score_song_for_query(song, query_tokens, first_token):
    """
    Heuristic score for a song given the query tokens.
    Higher = better.
    """
    score = 0

    # Title / slug
    title = song.name or ""
    slug = (song.slug or "").lower()

    title_tokens = _tokenize(title)

    # Authors
    author_tokens = []
    for a in song.authors.all():
        author_tokens.extend(_tokenize(a.name or ""))

    # Album
    album_name_tokens = []
    if song.album:
        album_name_tokens = _tokenize(song.album.name or "")

    # 1. Strong boost if first token matches start of slug or title
    if first_token:
        if title_tokens and title_tokens[0] == first_token:
            score += 120  # title starts with first word
        if slug.startswith(first_token):
            score += 150  # slug starts with first word

    # 2. Per-word matches
    matched_author_words = 0
    for w in query_tokens:
        if w in title_tokens:
            score += 12
        if w in author_tokens:
            score += 10
            matched_author_words += 1
        if w in album_name_tokens:
            score += 6

    # 3. Extra if at least two different author words match
    if matched_author_words >= 2:
        score += 30

    return score


def _rerank_songs_by_title_and_authors(hit_ids, songs, query: str):
    query_tokens = _tokenize(query)
    if not query_tokens:
        return hit_ids

    first_token = query_tokens[0]
    base_pos = {int(pk): pos for pos, pk in enumerate(hit_ids)}
    songs_by_id = {song.id: song for song in songs}

    scores = {}
    max_score = 0
    for pk in hit_ids:
        song = songs_by_id.get(pk)
        if not song:
            continue
        s = _score_song_for_query(song, query_tokens, first_token)
        scores[pk] = s
        if s > max_score:
            max_score = s

    # If our heuristics see nothing useful, keep pure ES order
    if max_score <= 0:
        return hit_ids

    ordered_ids = sorted(
        hit_ids,
        key=lambda pk: (-scores.get(pk, 0), base_pos.get(pk, 10**9)),
    )
    return ordered_ids


def search_song(query):
    if not query:
        return Song.objects.none()

    search = SongDocument.search()
    query = query.strip()
    terms = query.split()

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

    exact_queries = [
        ES_Q("term", **{"name.exact": {"value": query.lower(), "boost": 8}}),
        ES_Q("term", **{"slug.exact": {"value": query.lower(), "boost": 15}}),
    ]

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

    combined_queries = []
    if len(terms) >= 2:
        combined_queries.append(
            ES_Q(
                "bool",
                should=[
                    ES_Q("match", name={"query": query, "boost": 6}),
                    ES_Q(
                        "nested",
                        path="authors",
                        query=ES_Q(
                            "match", **{"authors.name": {"query": query, "boost": 5}}
                        ),
                    ),
                ],
                minimum_should_match=1,
                boost=12,
            )
        )
        combined_queries.append(
            ES_Q(
                "bool",
                should=[
                    ES_Q("match", name={"query": query, "boost": 6}),
                    ES_Q(
                        "nested",
                        path="album",
                        query=ES_Q(
                            "match", **{"album.name": {"query": query, "boost": 5}}
                        ),
                    ),
                ],
                minimum_should_match=1,
                boost=11,
            )
        )
    if len(terms) >= 3:
        combined_queries.append(
            ES_Q(
                "bool",
                should=[
                    ES_Q("match", name={"query": query, "boost": 6}),
                    ES_Q(
                        "nested",
                        path="authors",
                        query=ES_Q(
                            "match", **{"authors.name": {"query": query, "boost": 5}}
                        ),
                    ),
                    ES_Q(
                        "nested",
                        path="album",
                        query=ES_Q(
                            "match", **{"album.name": {"query": query, "boost": 4}}
                        ),
                    ),
                ],
                minimum_should_match=1,
                boost=13,
            )
        )

    main_queries = [
        ES_Q("match", name={"query": query, "boost": 5, "operator": "or"}),
        ES_Q(
            "match", name_transliterated={"query": query, "boost": 4, "operator": "or"}
        ),
        ES_Q("match", slug={"query": query, "boost": 6, "operator": "or"}),
        ES_Q(
            "nested",
            path="authors",
            query=ES_Q(
                "match",
                **{"authors.name": {"query": query, "boost": 4, "operator": "or"}},
            ),
        ),
        ES_Q(
            "nested",
            path="album",
            query=ES_Q(
                "match",
                **{"album.name": {"query": query, "boost": 3, "operator": "or"}},
            ),
        ),
    ]

    search_query = ES_Q(
        "bool",
        should=(
            main_queries
            + phrase_queries
            + exact_queries
            + fuzzy_queries
            + wildcard_queries
            + combined_queries
        ),
        minimum_should_match=1,
    )

    response = search.query(search_query).extra(size=20).execute()

    if not response.hits:
        return Song.objects.none()

    hit_ids = [hit.meta.id for hit in response.hits]
    hit_ids = _rerank_songs_by_title_and_authors(
        hit_ids, Song.objects.filter(id__in=hit_ids).prefetch_related("authors"), query
    )
    songs = Song.objects.filter(id__in=hit_ids).order_by(
        Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(hit_ids)])
    )
    return songs


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
