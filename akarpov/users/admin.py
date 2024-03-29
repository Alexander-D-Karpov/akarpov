from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import UserAPIToken

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("email",)}),
        (_("Images"), {"fields": ("image", "image_cropped")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Other"), {"fields": ("short_link", "left_file_upload")}),
    )
    list_display = ["username", "is_superuser"]
    search_fields = ["username", "email"]


@admin.register(UserAPIToken)
class UserAPITokenAdmin(admin.ModelAdmin):
    list_display = ["user", "active_until", "last_used"]
    search_fields = ["user__username", "token"]
    list_filter = ["active_until", "last_used"]
    date_hierarchy = "active_until"
    raw_id_fields = ["user"]
    actions = ["deactivate_tokens"]

    def deactivate_tokens(self, request, queryset):
        queryset.update(active_until=None)
        self.message_user(request, _("Tokens deactivated"))

    deactivate_tokens.short_description = _("Deactivate selected tokens")
