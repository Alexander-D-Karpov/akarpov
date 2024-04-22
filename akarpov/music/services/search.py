from django.core.cache import cache
from django.db.models import Case, When
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Q as ES_Q

from akarpov.music.documents import SongDocument
from akarpov.music.models import Song


def search_song(query):
    search = SongDocument.search()
    search_query = ES_Q(
        "bool",
        should=[
            # Boosting the exact matches using match_phrase
            ES_Q("bool", should=[ES_Q("match_phrase", name__exact=query)], boost=3),
            ES_Q(
                "bool",
                should=[ES_Q("match_phrase", name__raw=query.lower())],
                boost=2.5,
            ),  # Case-insensitive exact match with boost
            ES_Q("match", name__russian=query),
            ES_Q(
                "multi_match",
                query=query,
                fields=[
                    "name^5",
                    "name.russian^5",
                    "authors.name^3",
                    "authors.name.raw^3",
                    "album.name^3",
                    "album.name.raw^3",
                    "meta.*",  # Assuming dynamic mapping for meta fields
                ],
                type="best_fields",
                fuzziness="AUTO",
            ),
            ES_Q(
                "nested",
                path="authors",
                query=ES_Q(
                    "multi_match",
                    query=query,
                    fields=["authors.name", "authors.name.raw"],
                    fuzziness="AUTO",
                ),
                boost=2,
            ),
            ES_Q("wildcard", name__raw=f"*{query.lower()}*"),
            ES_Q("wildcard", meta__raw=f"*{query.lower()}*"),
        ],
        minimum_should_match=1,
    )

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
