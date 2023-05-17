from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models.functions import Collate

from .models import User

# Register your models here.
admin.site.register(User, UserAdmin)

class UserAdmin(UserAdmin):
    add_fieldsets = (
            (
                None,
                {
                    'classes': ('wide',),
                    'fields': ('username', 'email', 'password1', 'password2'),
                },
            ),
        )
    search_fields = ("email_deterministic","username_deterministic")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                email_deterministic=Collate("email", "und-x-icu"),
                username_deterministic=Collate("username", "und-x-icu"),
            )
        )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)