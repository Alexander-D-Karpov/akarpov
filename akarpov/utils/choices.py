from collections.abc import Iterable

from django.db.models.enums import ChoicesMeta


def count_max_length(choices: Iterable | ChoicesMeta):
    if isinstance(choices, ChoicesMeta):
        return max([len(val) for val in choices.values])
    return max([len(val) for val, _ in choices])
