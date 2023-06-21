from django.db import models
from model_utils.models import TimeStampedModel


class PromoCode(TimeStampedModel):
    class PromoCodeType(models.TextChoices):
        single = "single", "can be activated only one time, by one user"
        multiuser = (
            "multiuser",
            "can be activated many times, but only one time for one user",
        )
        multiple = "multiple", "can be activated multiple times"

    promo = models.CharField(max_length=250, unique=True)
    type = models.CharField(choices=PromoCodeType.choices)
    name = models.CharField(max_length=250)
    app_name = models.CharField(max_length=250)
    model = models.CharField(max_length=250)
    field = models.CharField(max_length=250)
    value = models.IntegerField()
    message = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class PromoCodeActivation(models.Model):
    activated = models.DateTimeField(auto_now_add=True)
    promocode = models.ForeignKey(
        "PromoCode", related_name="activations", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        "users.User", related_name="promocode_activations", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.promocode} activation by {self.user}"
