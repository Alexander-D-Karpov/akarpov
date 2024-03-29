from django import forms
from django_ckeditor_5.fields import CKEditor5Field
from django_ckeditor_5.widgets import CKEditor5Widget

from akarpov.blog.models import Post, Tag


class PostForm(forms.ModelForm):
    body = CKEditor5Field(config_name="extends")
    image = forms.ImageField(help_text="better use horizontal images", required=False)
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple, required=True
    )

    class Meta:
        model = Post
        fields = ["title", "body", "image", "tags"]
        widgets = {
            "body": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"},
                config_name="extends",
            )
        }
