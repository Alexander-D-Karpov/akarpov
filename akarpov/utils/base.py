from django.contrib.contenttypes.models import ContentType


def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)]
    )


class SubclassesMixin:
    @classmethod
    def get_subclasses(cls):
        content_types = ContentType.objects.filter(app_label=cls._meta.app_label)
        models = [ct.model_class() for ct in content_types]
        return [
            model
            for model in models
            if (model is not None and issubclass(model, cls) and model is not cls)
        ]
