from django.db.models import QuerySet


def batch_qs(qs: QuerySet, batch_size: int = 1000):
    total = qs.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield from qs[start:end]
