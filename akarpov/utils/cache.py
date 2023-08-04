from django.db.models import Model

stack = {}


def cache_model_property(model: Model, name: str):
    # function to store non-hashable value for model instances
    # TODO: add TTL here and update with celery

    app_name = model._meta.app_label + model._meta.model_name
    if app_name not in stack:
        stack[app_name] = {}

    if model.pk not in stack[app_name]:
        stack[app_name][model.pk] = {}

    if name not in stack[app_name][model.pk]:
        val = getattr(model, name)
        if callable(val):
            val = val()
        stack[app_name][model.pk][name] = val
        return val
    return stack[app_name][model.pk][name]


def clear_model_cache(model: Model, name=None):
    app_name = model._meta.app_label + model._meta.model_name
    if app_name not in stack:
        return

    if model.pk not in stack[app_name]:
        return

    if name:
        if name in stack[app_name][model.pk]:
            del stack[app_name][model.pk][name]
    else:
        del stack[app_name][model.pk]
    return
