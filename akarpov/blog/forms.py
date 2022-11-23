from ckeditor.fields import RichTextFormField
from django import forms

from akarpov.blog.models import Post, Tag


class PostForm(forms.ModelForm):
    body = RichTextFormField(label="")
    image = forms.ImageField(help_text="better use horizontal images", required=False)
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple, required=True
    )

    class Meta:
        model = Post
        fields = ["title", "body", "image", "tags"]
