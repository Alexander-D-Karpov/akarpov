from django.views.generic import CreateView

from akarpov.tools.qr.forms import QRForm
from akarpov.tools.qr.models import QR


class QRCreateView(CreateView):
    model = QR
    form_class = QRForm

    template_name = "tools/qr/create.html"

    def form_valid(self, form):
        form.instance.user = self.request.user if self.request.user else None
        return super().form_valid(form)


qr_create_view = QRCreateView.as_view()
