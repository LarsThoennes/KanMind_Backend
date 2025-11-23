from django.db.models import Q
from rest_framework import generics, status
from ..models import Task, Comment
from .serializers import TaskSerializer, CommentSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

class TasksView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user 
        return Task.objects.filter(
            Q(owner=user) 
              | Q(assignee=user) 
              | Q(reviewer=user) 
        ).distinct() 

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/tasks/<task_id>/        → Einzelne Task abrufen
    PATCH  /api/tasks/<task_id>/        → Task teilweise aktualisieren
    PUT    /api/tasks/<task_id>/        → Task vollständig aktualisieren
    DELETE /api/tasks/<task_id>/        → Task löschen
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        task_id = self.kwargs["task_id"]

        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound("Task nicht gefunden.")

        user = self.request.user
        if not (task.owner == user or task.assignee == user or task.reviewer == user):
            raise PermissionDenied("Du darfst diese Task nicht bearbeiten oder löschen.")

        return task

    def patch(self, request, *args, **kwargs):
        """PATCH: Teilaktualisierung einer Task"""
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """PUT: Komplette Aktualisierung"""
        return self.update(request, *args, **kwargs)


class TaskCommentsView(generics.ListCreateAPIView):
    """
    GET  -> gibt alle Kommentare einer Task zurück
    POST -> erstellt einen neuen Kommentar für die Task
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_task(self):
        """Holt die Task oder wirft 404, falls sie nicht existiert."""
        try:
            return Task.objects.get(pk=self.kwargs["task_id"])
        except Task.DoesNotExist:
            raise NotFound(detail="Task nicht gefunden. Die angegebene Task-ID existiert nicht.")

    def get_queryset(self):
        """Liefert alle Kommentare zur Task, sofern der User Zugriff hat."""
        task = self.get_task()
        user = self.request.user

        if not (task.owner == user or task.assignee == user or task.reviewer == user):
            raise PermissionDenied("Du darfst die Kommentare dieser Task nicht sehen.")

        return Comment.objects.filter(task=task).order_by("created_at")

    def perform_create(self, serializer):
        """Erstellt neuen Kommentar (POST)."""
        task = self.get_task()
        user = self.request.user

        if not (task.owner == user or task.assignee == user or task.reviewer == user):
            raise PermissionDenied("Du darfst zu dieser Task keinen Kommentar hinzufügen.")

        content = self.request.data.get("content")
        if not content or not content.strip():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"content": "Der Kommentartext darf nicht leer sein."})

        serializer.save(author=user, task=task)

class TaskCommentDetailView(generics.DestroyAPIView):
    """
    DELETE /api/tasks/<task_id>/comments/<comment_id>/
    Löscht einen Kommentar, wenn der User berechtigt ist.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        task_id = self.kwargs["task_id"]
        comment_id = self.kwargs["comment_id"]

        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound("Task nicht gefunden.")

        try:
            comment = Comment.objects.get(pk=comment_id, task=task)
        except Comment.DoesNotExist:
            raise NotFound("Kommentar nicht gefunden.")

        user = self.request.user

        if not (comment.author == user or task.owner == user):
            raise PermissionDenied("Du darfst diesen Kommentar nicht löschen.")

        return comment

    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class TasksAssignedToMeView(generics.ListAPIView):
    """
    GET /api/tasks/assigned-to-me/
    Gibt alle Tasks zurück, die dem aktuell eingeloggten Benutzer zugewiesen sind.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Task.objects
            .filter(assignee=user)
            .select_related("board", "assignee", "reviewer")
            .order_by("due_date")
        )
    
class TasksReviewingView(generics.ListAPIView):
    """
    GET /api/tasks/reviewing/
    Gibt alle Tasks zurück, bei denen der eingeloggte Benutzer Reviewer ist.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Task.objects
            .filter(reviewer=user)
            .select_related("board", "assignee", "reviewer")
            .order_by("due_date")
        )
