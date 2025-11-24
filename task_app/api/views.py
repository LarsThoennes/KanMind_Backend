from django.db.models import Q
from rest_framework import generics, status
from ..models import Task, Comment
from .serializers import TaskSerializer, CommentSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

class TasksView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(owner=user) | Q(assignee=user) | Q(reviewer=user)
        ).distinct()

    def perform_create(self, serializer):
        """
        Nur Mitglieder oder Owner des Boards dürfen eine Task erstellen.
        """
        user = self.request.user
        board = serializer.validated_data.get("board")

        if not (board.owner == user or board.members.filter(id=user.id).exists()):
            raise PermissionDenied("Du darfst in diesem Board keine Task erstellen.")

        serializer.save(owner=user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        task_id = self.kwargs.get("task_id")
        task = get_object_or_404(Task, pk=task_id)

        user = self.request.user
        if not (task.owner == user or task.assignee == user or task.reviewer == user):
            raise PermissionDenied("Du darfst diese Task nicht ansehen, bearbeiten oder löschen.")

        return task

    def patch(self, request, *args, **kwargs):
        """PATCH: Teilaktualisierung einer Task"""
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """PUT: Komplette Aktualisierung"""
        return self.update(request, *args, **kwargs)


class TaskCommentsView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_task(self):
        task_id = self.kwargs.get("task_id")
        task = get_object_or_404(Task, pk=task_id)
        return task

    def get_queryset(self):
        """Liefert alle Kommentare zur Task, sofern der User Zugriff hat."""
        task = self.get_task()
        user = self.request.user

        if not (task.owner == user or task.assignee == user or task.reviewer == user):
            raise PermissionDenied("Du darfst die Kommentare dieser Task nicht sehen.")

        queryset = Comment.objects.filter(task=task).order_by("created_at")

        # 🔥 Wenn keine Kommentare vorhanden sind → 404
        if not queryset.exists():
            raise NotFound("Keine Kommentare für diese Task gefunden.")

        return queryset

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

        task = get_object_or_404(Task, pk=task_id)
        comment = get_object_or_404(Comment, pk=comment_id, task=task)

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
