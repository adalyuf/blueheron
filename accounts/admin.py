from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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

admin.site.unregister(User)
admin.site.register(User, UserAdmin)