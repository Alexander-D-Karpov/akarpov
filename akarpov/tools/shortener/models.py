from abc import abstractmethod

from django.db import models
from django.urls import reverse
from model_utils.models import TimeStampedModel

from akarpov.common.models import SlugModel


class Link(TimeStampedModel):
    source = models.URLField(blank=False)
    slug = models.SlugField(db_index=True, unique=False)
    creator = models.ForeignKey(
        "users.User", related_name="links", null=True, on_delete=models.SET_NULL
    )
    enabled = models.BooleanField(default=True)

    viewed = models.IntegerField(default=0)

    @property
    def full_source(self):
        return (
            "https://akarpov.ru" + self.source
            if self.source.startswith("/")
            else self.source
        )

    def get_absolute_url(self):
        return reverse("tools:shortener:view", kwargs={"slug": self.slug})

    def __str__(self):
        return f"link to {self.source}"

    class Meta:
        ordering = ["-modified"]
        db_table = "short_link"


class LinkViewMeta(models.Model):
    # TODO: move to mem, delete within 7 days
    link = models.ForeignKey(Link, related_name="views", on_delete=models.CASCADE)

    viewed = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=200)
    user = models.ForeignKey(
        "users.User", related_name="link_views", null=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["-viewed"]

    def __str__(self):
        return f"view on {self.link.source}"


def create_model_link(sender, instance, created, **kwargs):
    # had to move to models due to circular import
    # TODO: add link create to celery
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
        elif hasattr(instance, "user"):
            link.creator = instance.user
        elif hasattr(instance, "owner"):
            link.creator = instance.owner

        link.save()
        instance.short_link = link
        instance.save()


def update_model_link(sender, instance, **kwargs):
    model = sender
    if instance.id:
        previous = model.objects.get(id=instance.id)
        prev_private = False
        cur_private = False
        if hasattr(instance, "private"):
            if instance.private:
                cur_private = True
        if hasattr(instance, "public"):
            if not instance.public:
                cur_private = True
        if hasattr(previous, "private"):
            if previous.private:
                prev_private = True
        if hasattr(previous, "public"):
            if not previous.public:
                prev_private = True

        if prev_private != cur_private:
            if prev_private:
                # instance was private, public now, need to create short link
                if hasattr(instance, "short_link"):
                    if not instance.short_link:
                        link = Link(source=instance.get_absolute_url())
                        if hasattr(instance, "creator"):
                            link.creator = instance.creator
                        elif hasattr(instance, "user"):
                            link.creator = instance.user
                        elif hasattr(instance, "owner"):
                            link.creator = instance.owner
                        link.save()
                        instance.short_link = link
            else:
                # instance was public, private now, need to delete short link
                if hasattr(previous, "short_link"):
                    if previous.short_link:
                        previous.short_link.delete()
                        instance.short_link = None


class ShortLinkModel(SlugModel):
    short_link: Link | None = models.ForeignKey(
        "shortener.Link", blank=True, null=True, on_delete=models.SET_NULL
    )

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        models.signals.post_save.connect(create_model_link, sender=cls)
        models.signals.pre_save.connect(update_model_link, sender=cls)

    @abstractmethod
    def get_absolute_url(self):
        raise NotImplementedError

    @property
    def get_short_link(self) -> str:
        if self.short_link:
            return reverse("short_url", kwargs={"slug": self.short_link.slug})
        return reverse("tools:shortener:revoked")

    class Meta:
        abstract = True
