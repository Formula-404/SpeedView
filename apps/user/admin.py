from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile

class ReadOnlyMixin:
    actions = None
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def has_view_permission(self, request, obj=None):
        return True
    def get_readonly_fields(self, request, obj=None):
        names = [f.name for f in self.model._meta.fields]
        names += [m.name for m in self.model._meta.many_to_many]
        return tuple(sorted(set(names + list(getattr(self, 'readonly_fields', [])))))

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('role', 'theme_preference', 'created_at', 'updated_at')
    readonly_fields = ('role', 'theme_preference', 'created_at', 'updated_at')
    extra = 0
    max_num = 0

class UserAdmin(ReadOnlyMixin, BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_display_links = None

    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return '-'
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'

@admin.register(UserProfile)
class UserProfileAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('get_username', 'role', 'theme_preference', 'created_at', 'updated_at')
    list_filter = ('role', 'theme_preference', 'created_at')
    search_fields = ('id__username', 'id__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_display_links = None

    def get_username(self, obj):
        return obj.id.username
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'id__username'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.disable_action('delete_selected')
