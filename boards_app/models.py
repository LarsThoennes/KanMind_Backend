from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Board(models.Model):
    title = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_boards")
    members = models.ManyToManyField(User, related_name="boards")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
