from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel


class Project(TimeStampedModel):
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    md = models.TextField(blank=True)
    image = models.ImageField(upload_to="uploads/images/", blank=False)
    source_link = models.URLField(blank=True)
    view_link = models.URLField(blank=True)

    def get_absolute_url(self):
        return reverse("about:project", kwargs={"pk": self.pk})

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("-modified",)


class ProjectChange(models.Model):
    project = models.ForeignKey(
        "Project", related_name="changes", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=150)
    created = models.DateTimeField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("-created",)
