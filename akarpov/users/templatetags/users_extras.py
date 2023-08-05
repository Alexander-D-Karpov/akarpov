from django import template

from akarpov.users.models import User

register = template.Library()


@register.inclusion_tag("users/badge.html", name="user_badge")
def user_badge(user: User):
    return {"user": user}
