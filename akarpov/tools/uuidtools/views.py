import uuid

import uuid6
from django.utils.timezone import now
from django.views import generic

from akarpov.tools.uuidtools.services import decode_uuid


class MainView(generic.TemplateView):
    template_name = "tools/uuid/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "uuid" in self.request.GET:
            data = decode_uuid(str(self.request.GET["uuid"]))
            context["data"] = data
            context["uuid"] = self.request.GET["uuid"]

        context["tokens"] = [
            (uuid.uuid4(), 4),
            (uuid6.uuid6(), 6),
            (uuid6.uuid8(), 8),
            (uuid.uuid1(), 1),
        ]
        context["now"] = now()
        return context
