from django.db import models
from django.contrib.auth import get_user_model
from boards_app.models import Board

User = get_user_model()

class Task(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=1000)
    
    status = models.CharField(max_length=20)
    priority = models.CharField(max_length=20)
    
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks")
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_tasks")
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_tasks")
    
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()

    def __str__(self):
        return self.title

class Comment(models.Model):
    task = models.ForeignKey(Task, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} - {self.task.title[:20]}"