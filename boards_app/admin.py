from django.contrib import admin
from .models import Board

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "member_list", "created_at")
    search_fields = ("title", "owner__username", "members__username")

    def member_list(self, obj):
        return ", ".join([user.username for user in obj.members.all()])
    member_list.short_description = "Members"
