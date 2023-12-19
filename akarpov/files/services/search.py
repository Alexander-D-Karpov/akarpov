import os
import re
from typing import BinaryIO

from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, F, FloatField, Func, Q, QuerySet, Value, When
from django.db.models.functions import Coalesce
from elasticsearch_dsl import Q as ES_Q

from akarpov.files.models import File

from ..documents import FileDocument
from .lema import lemmatize_and_remove_stopwords

"""
Calculus on types of searches:
https://new.akarpov.ru/files/FZUTFBIyfbdlDHVzxUNU
"""


class BaseSearch:
    def __init__(self, queryset: QuerySet | None = None):
        self.queryset: QuerySet | None = queryset

    def search(self, query: str) -> QuerySet | list[File]:
        raise NotImplementedError("Subclasses must implement this method")


class NeuroSearch(BaseSearch):
    def search(self, query: str):
        if not self.queryset:
            raise ValueError("Queryset cannot be None for search")

        # Perform the Elasticsearch query using a combination of match, match_phrase_prefix, and wildcard queries
        search = FileDocument.search()
        search_query = ES_Q(
            "bool",
            should=[
                ES_Q(
                    "multi_match",
                    query=query,
                    fields=["name", "description", "content"],
                    type="best_fields",
                ),
                ES_Q("match_phrase_prefix", name=query),
                ES_Q("wildcard", name=f"*{query}*"),
                ES_Q("wildcard", description=f"*{query}*"),
                ES_Q("wildcard", content=f"*{query}*"),
            ],
            minimum_should_match=1,
        )

        search = search.query(search_query)

        # Execute the search to get the results
        response = search.execute()

        # Check if there are hits, if not return an empty queryset
        if not response.hits:
            return self.queryset.none()

        # Collect the IDs of the hits
        hit_ids = [hit.meta.id for hit in response.hits]

        # Use the hit IDs to filter the queryset and preserve the order
        preserved_order = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(hit_ids)]
        )
        relevant_queryset = self.queryset.filter(pk__in=hit_ids).order_by(
            preserved_order
        )

        return relevant_queryset


class CaseSensitiveSearch(BaseSearch):
    def search(self, query: str) -> QuerySet[File]:
        if self.queryset is None:
            raise ValueError("Queryset cannot be None for text search")

        # Escape any regex special characters in the query string
        query_escaped = re.escape(query)

        # Use a case-sensitive regex to filter
        return self.queryset.filter(
            Q(name__regex=query_escaped)
            | Q(description__regex=query_escaped)
            | Q(content__regex=query_escaped)
        )


class ByteSearch(BaseSearch):
    def search(self, hex_query: str) -> list[File]:
        # Convert the hex query to bytes
        try:
            byte_query: bytes = bytes.fromhex(hex_query)
        except ValueError:
            # If hex_query is not a valid hex, return an empty list
            return []

        matching_files: list[File] = []
        if self.queryset is not None:
            for file_item in self.queryset:
                file_path: str = file_item.file.path
                full_path: str = os.path.join(settings.MEDIA_ROOT, file_path)
                if os.path.exists(full_path):
                    with open(full_path, "rb") as file:
                        if self._byte_search_in_file(file, byte_query):
                            matching_files.append(file_item)
        return matching_files

    @staticmethod
    def _byte_search_in_file(file: BinaryIO, byte_sequence: bytes) -> bool:
        # Read the file in chunks to avoid loading large files into memory
        chunk_size: int = 4096  # or another size depending on the expected file sizes
        while True:
            chunk: bytes = file.read(chunk_size)
            if byte_sequence in chunk:
                return True
            if not chunk:  # End of file reached
                return False


class UnaccentLower(Func):
    function = "UNACCENT"

    def as_sql(self, compiler, connection):
        unaccented_sql, unaccented_params = compiler.compile(
            self.get_source_expressions()[0]
        )
        lower_unaccented_sql = f"LOWER({unaccented_sql})"
        return lower_unaccented_sql, unaccented_params


class SimilaritySearch(BaseSearch):
    def search(self, query: str) -> QuerySet[File]:
        if self.queryset is None:
            raise ValueError("Queryset cannot be None for similarity search")

        language = "russian" if re.search("[а-яА-Я]", query) else "english"
        filtered_query = lemmatize_and_remove_stopwords(query, language=language)
        queryset = (
            self.queryset.annotate(
                name_similarity=Coalesce(
                    TrigramSimilarity(UnaccentLower("name"), filtered_query),
                    Value(0),
                    output_field=FloatField(),
                ),
                description_similarity=Coalesce(
                    TrigramSimilarity(UnaccentLower("description"), filtered_query),
                    Value(0),
                    output_field=FloatField(),
                ),
                content_similarity=Coalesce(
                    TrigramSimilarity(UnaccentLower("content"), filtered_query),
                    Value(0),
                    output_field=FloatField(),
                ),
            )
            .annotate(
                combined_similarity=(
                    F("name_similarity")
                    + F("description_similarity")
                    + F("content_similarity")
                )
            )
            .filter(combined_similarity__gt=0.1)
            .order_by("-combined_similarity")
        )

        return queryset
