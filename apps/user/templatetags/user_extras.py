from django import template

register = template.Library()


@register.filter
def is_admin_user(user):
    if user is None:
        return False
    if getattr(user, "is_superuser", False):
        return True
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None) == "admin"
