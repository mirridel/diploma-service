from django.contrib import admin

from car_service.apps.customuser.models import User


class CustomUserAdmin(admin.ModelAdmin):
    username = None


admin.site.register(User, CustomUserAdmin)
