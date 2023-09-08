from django.utils.module_loading import autodiscover_modules
from pytest_factoryboy.fixture import get_caller_locals, register


class RegisteredFactory:
    def __init__(self, factory_class, args, kwargs):
        self.factory_class = factory_class
        self.args = args
        self.kwargs = kwargs


factory_registry = set()  # set of registered factories


def global_register(factory_class=None, *args, **kwargs):
    if factory_class is None:

        def _global_register(factory_class):
            return global_register(factory_class, *args, **kwargs)

        return _global_register

    factory_registry.add(RegisteredFactory(factory_class, args, kwargs))

    return factory_class


def autodiscover_factories():
    assert (
        not factory_registry
    ), "You've already called `autodiscover_factories` function"

    caller_locals = get_caller_locals()

    assert caller_locals["__name__"].endswith(
        "conftest"
    ), "You must call `autodiscover_factories` from `conftest.py` file"

    autodiscover_modules("tests.factories")

    for registered_factory in factory_registry:
        register(
            registered_factory.factory_class,
            *registered_factory.args,
            _caller_locals=caller_locals,
            **registered_factory.kwargs,
        )
