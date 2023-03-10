from decimal import Decimal as D

from faker.providers.python import Provider as PythonProvider


class MoneyProvider(PythonProvider):
    def money(self):
        return self.pydecimal(right_digits=2, min_value=D(1), max_value=D(1000))


additional_providers = [MoneyProvider]


def configure_factory_faker(factory_faker):
    factory_faker._DEFAULT_LOCALE = "ru_RU"
    for provider in additional_providers:
        factory_faker.add_provider(provider, locale="ru_RU")


def configure_faker(faker):
    for provider in additional_providers:
        faker.add_provider(provider)
