from django.db import models
from django.urls import reverse
from model_utils.models import TimeStampedModel


class Link(TimeStampedModel):
    source = models.URLField(blank=False)
    slug = models.SlugField()

    creator = models.ForeignKey(
        "users.User", related_name="links", null=True, on_delete=models.SET_NULL
    )
    enabled = models.BooleanField(default=True)

    viewed = models.IntegerField(default=0)

    def get_absolute_url(self):
        return reverse("short_url", kwargs={"slug": self.slug})

    def __str__(self):
        return f"link to {self.source}"


class LinkViewMeta(models.Model):
    # TODO: move to mem, delete within 7 days
    link = models.ForeignKey(Link, related_name="views", on_delete=models.CASCADE)

    viewed = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=200)

    def __str__(self):
        return f"view on {self.link.source}"
