from django.contrib import admin
from .models import Task, Comment

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "owner", "assignee", "reviewer", "due_date")
    search_fields = ("title", "description")
    list_filter = ("status", "priority")
    ordering = ("-id",)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "author", "created_at", "content")
    search_fields = ("content",)
    list_filter = ("created_at",)
