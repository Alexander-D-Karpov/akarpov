import structlog
from django.apps import apps

from akarpov.tools.promocodes.models import PromoCode, PromoCodeActivation
from akarpov.users.models import User

logger = structlog.get_logger(__name__)


def activate_promocode(code: str, user: User) -> (str, bool):
    try:
        promo = PromoCode.objects.get(promo=code)
    except PromoCode.DoesNotExist:
        return "Promocode doesn't exist", False

    if promo.type == PromoCode.PromoCodeType.single:
        if PromoCodeActivation.objects.filter(promocode=promo).exists():
            return "Promocode is already activated", False
    elif promo.type == PromoCode.PromoCodeType.multiuser:
        if PromoCodeActivation.objects.filter(promocode=promo, user=user).exists():
            return "Promocode is already activated", False
    try:
        model = apps.get_model(app_label=promo.app_name, model_name=promo.model)
    except LookupError:
        logger.error(
            f"can't activate promocode {code} for {promo.model} {promo.app_name} {promo.field}"
        )
        return "Somthing went wrong, we are already working on it", False

    if not hasattr(model, promo.field):
        logger.error(
            f"can't activate promocode {code} for {promo.model} {promo.app_name} {promo.field}"
        )
        return "Somthing went wrong, we are already working on it", False
    if model is User:
        try:
            setattr(user, promo.field, getattr(user, promo.field) + promo.value)
            user.save()
            PromoCodeActivation.objects.create(promocode=promo, user=user)
            return promo.message, True
        except Exception as e:
            logger.error(
                f"can't activate promocode {code} for {promo.model} {promo.app_name} {promo.field}, {e}"
            )
            return "Somthing went wrong, we are already working on it", False
    else:
        try:
            usr_field = ""
            if hasattr(model, "user"):
                usr_field = "user"
            elif hasattr(model, "creator"):
                usr_field = "creator"
            elif hasattr(model, "owner"):
                usr_field = "owner"
            obj = model.objects.filter({usr_field: user}).last()
            setattr(obj, promo.field, getattr(obj, promo.field) + promo.value)
            obj.save()
            PromoCodeActivation.objects.create(promocode=promo, user=user)
            return promo.message, True
        except Exception as e:
            logger.error(
                f"can't activate promocode {code} for {promo.model} {promo.app_name} {promo.field}, {e}"
            )
            return "Somthing went wrong, we are already working on it", False
