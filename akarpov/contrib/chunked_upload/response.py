from django.http import HttpResponse

from .settings import CONTENT_TYPE, ENCODER


class Response(HttpResponse):
    """ """

    def __init__(self, content, status=None, *args, **kwargs):
        super().__init__(
            content=ENCODER(content),
            content_type=CONTENT_TYPE,
            status=status,
            *args,
            **kwargs
        )
