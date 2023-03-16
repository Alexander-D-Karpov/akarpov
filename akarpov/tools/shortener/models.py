from abc import abstractmethod

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


def create_model_link(sender, instance, created, **kwargs):
    # had to move to models due to circular import
    if created:
        link = Link(source=instance.get_absolute_url())
        if hasattr(instance, "private"):
            if instance.private:
                return
        if hasattr(instance, "public"):
            if not instance.public:
                return
        if hasattr(instance, "creator"):
            link.creator = instance.creator

        link.save()
        instance.short_link = link
        instance.save()


class ShortLink(models.Model):
    short_link: Link | None = models.ForeignKey(
        "shortener.Link", blank=True, null=True, on_delete=models.SET_NULL
    )

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        models.signals.post_save.connect(create_model_link, sender=cls)

    @abstractmethod
    def get_absolute_url(self):
        ...

    @property
    def get_short_link(self) -> str:
        if self.short_link:
            return reverse("short_url", kwargs={"slug": self.short_link.slug})
        return reverse("tools:shortener:revoked")

    class Meta:
        abstract = True
