import factory.fuzzy
from factory.django import DjangoModelFactory

from akarpov.utils.pytest_factoryboy import global_register


@global_register
class UserFactory(DjangoModelFactory):
    email = factory.Sequence(lambda i: f"user_{i}@akarpov.ru")
    username = factory.Faker("word")
    image = factory.fuzzy.FuzzyText(prefix="https://img")
    password = "P@ssw0rd"

    class Meta:
        model = "users.User"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)
