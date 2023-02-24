import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel

from akarpov.users.models import User
from akarpov.utils.files import user_file_upload_mixin


class Form(models.Model):
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=True)

    creator = models.ForeignKey("users.User", on_delete=models.CASCADE)
    slug = models.SlugField(max_length=20, blank=True)

    public = models.BooleanField(default=True)
    anyone_can_access = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    image = models.ImageField(upload_to=user_file_upload_mixin, blank=True)
    image_cropped = models.ImageField(upload_to="cropped/", blank=True)

    passed = models.IntegerField(default=0)
    time_till = models.DateTimeField(null=True, blank=True)

    @property
    def available(self) -> bool:
        return (
            self.time_till.timestamp() >= timezone.now().timestamp()
            if self.time_till
            else True
        )

    def __str__(self):
        return f"form: {self.name}"


class BaseQuestion(PolymorphicModel):
    type = _("No type")
    form: Form = models.ForeignKey(
        "test_platform.Form", related_name="fields", on_delete=models.CASCADE
    )
    question = models.CharField(max_length=250, blank=False)
    help = models.CharField(max_length=200, blank=True)
    required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.type} - {self.question}"


class TextQuestion(BaseQuestion):
    type = _("Text question")
    correct_answer = models.CharField(max_length=250, blank=False)
    answer_should_contain = models.CharField(max_length=250, blank=False)
    answer_should_not_contain = models.CharField(max_length=250, blank=False)


class NumberQuestion(BaseQuestion):
    type = _("Number question")
    correct_answer = models.IntegerField()


class NumberRangeQuestion(BaseQuestion):
    type = _("Number question")
    number_range_min = models.IntegerField(blank=False)
    number_range_max = models.IntegerField(blank=False)


class SelectQuestion(BaseQuestion):
    min_required_answers = models.IntegerField(blank=False)
    max_required_answers = models.IntegerField(blank=False)


class SelectAnswerQuestion(models.Model):
    id: uuid.UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    value = models.CharField(max_length=150)
    correct = models.BooleanField(null=True)


class FormPermission(models.Model):
    form: Form = models.ForeignKey(
        "test_platform.Form", related_name="allowed", on_delete=models.CASCADE
    )
    user: User = models.ForeignKey(
        "users.User", related_name="allowed_test_platform", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ["form", "user"]

    def __str__(self):
        return f"user {self.user.username} can access {self.form.name}"


class FormHistory(models.Model):
    form: Form = models.ForeignKey(
        "test_platform.Form", related_name="users_opened", on_delete=models.CASCADE
    )
    user: User = models.ForeignKey(
        "users.User", related_name="opened_test_platform", on_delete=models.CASCADE
    )
    opened = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"user {self.user.username} opened form {self.form.name} at {self.opened}"
        )
