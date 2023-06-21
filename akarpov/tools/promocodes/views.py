from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from akarpov.tools.promocodes.forms import PromoCodeForm
from akarpov.tools.promocodes.services import activate_promocode


class ActivatePromoCodeView(LoginRequiredMixin, generic.FormView):
    form_class = PromoCodeForm
    template_name = "tools/promocodes/activate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = ""
        context["status"] = False
        return context

    def form_valid(self, form):
        msg, status = activate_promocode(form.data["promocode"], self.request.user)
        context = self.get_context_data(form=form)
        context["message"] = msg
        context["status"] = status
        return self.render_to_response(context=context)


activate_promo_code = ActivatePromoCodeView.as_view()
