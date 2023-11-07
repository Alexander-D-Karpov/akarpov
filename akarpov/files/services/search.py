import os
import re
from typing import BinaryIO

from django.conf import settings
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q, QuerySet
from haystack.query import SearchQuerySet

from akarpov.files.models import File


class BaseSearch:
    def __init__(self, queryset: QuerySet | None = None):
        self.queryset: QuerySet | None = queryset

    def search(self, query: str) -> QuerySet | SearchQuerySet | list[File]:
        raise NotImplementedError("Subclasses must implement this method")


class NeuroSearch(BaseSearch):
    def search(self, query: str) -> SearchQuerySet:
        # Search across multiple fields
        sqs: SearchQuerySet = SearchQuerySet().filter(content=query)
        sqs = sqs.filter_or(name=query)
        sqs = sqs.filter_or(description=query)
        return sqs


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


class SimilaritySearch(BaseSearch):
    def __init__(self, queryset: QuerySet[File] | None = None):
        super().__init__(queryset)

    def search(self, query: str) -> QuerySet[File]:
        if self.queryset is None:
            raise ValueError("Queryset cannot be None for similarity search")

        # Perform a similarity search using trigram comparison
        return (
            self.queryset.annotate(
                name_unaccent=Unaccent("name"),
                description_unaccent=Unaccent("description"),
                content_unaccent=Unaccent("content"),
            )
            .annotate(
                similarity=TrigramSimilarity("name_unaccent", query)
                + TrigramSimilarity("description_unaccent", query)
                + TrigramSimilarity("content_unaccent", query)
            )
            .filter(similarity__gt=0.1)
            .order_by("-similarity")
        )
