from django.contrib import admin

from akarpov.blog.models import Post, PostRating, Tag


class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "post_views")
    list_filter = ("creator",)
    readonly_fields = ("created", "edited")
    fieldsets = (
        (None, {"fields": ("title", "body", "creator", "tags")}),
        (
            "Ratings",
            {
                "classes": ("collapse",),
                "fields": (
                    "post_views",
                    "rating",
                    "rating_up",
                    "rating_down",
                    "comment_count",
                ),
            },
        ),
        (
            "Images",
            {
                "classes": ("collapse",),
                "fields": ("image", "image_cropped"),
            },
        ),
        (
            "Urls",
            {
                "classes": ("collapse",),
                "fields": ("slug", "short_link"),
            },
        ),
    )


admin.site.register(Post, PostAdmin)
admin.site.register(Tag)
admin.site.register(PostRating)
