from collections.abc import Iterable

from django.db.models import QuerySet

from .query import batch_qs


def progress_tracker(
    a_list: list, a_len: int = 0, step: int = 10, template: str = "Done %d/%d"
) -> Iterable:
    if not a_len:
        a_len = len(a_list)
    for n, item in enumerate(a_list):
        if n % step == 0:
            print(template % (n, a_len))
        yield item


def iterate_big_queryset(
    qs: QuerySet, batch_size: int = 1000, step: int = 10
) -> Iterable:
    return progress_tracker(
        a_list=batch_qs(qs, batch_size=batch_size),
        a_len=qs.count(),
        step=step,
    )
