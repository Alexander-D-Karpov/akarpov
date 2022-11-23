from django.contrib import admin

from akarpov.blog.models import Post, PostRating, Tag

# Register your models here.


admin.site.register(Post)
admin.site.register(Tag)
admin.site.register(PostRating)
