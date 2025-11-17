from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()

# Erst das Standard-Admin für User abmelden
admin.site.unregister(User)

# Jetzt neu registrieren mit eigener Darstellung
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "email", "is_staff", "is_superuser")
    search_fields = ("username", "email")
    ordering = ("id",)
