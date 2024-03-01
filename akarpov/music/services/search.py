from django.db.models import Case, When
from elasticsearch_dsl import Q as ES_Q

from akarpov.music.documents import SongDocument
from akarpov.music.models import Song


def search_song(query):
    search = SongDocument.search()
    search_query = ES_Q(
        "bool",
        should=[
            ES_Q(
                "multi_match",
                query=query,
                fields=["name^5", "authors.name^3", "album.name^3"],
                fuzziness="AUTO",
            ),
            ES_Q("wildcard", name__raw=f"*{query.lower()}*"),
            ES_Q(
                "nested",
                path="authors",
                query=ES_Q("wildcard", authors__name__raw=f"*{query.lower()}*"),
            ),
            ES_Q(
                "nested",
                path="album",
                query=ES_Q("wildcard", album__name__raw=f"*{query.lower()}*"),
            ),
            ES_Q("wildcard", meta__raw=f"*{query.lower()}*"),
        ],
        minimum_should_match=1,
    )

    search = search.query(search_query)

    response = search.execute()

    # Check for hits and get song instances
    if response.hits:
        hit_ids = [hit.meta.id for hit in response.hits]
        songs = Song.objects.filter(id__in=hit_ids).order_by(
            Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(hit_ids)])
        )

        return songs

    return Song.objects.none()
