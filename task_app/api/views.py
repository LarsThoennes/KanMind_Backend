from django.db.models import Q
from rest_framework import generics, status
from ..models import Task, Comment
from .serializers import TaskSerializer, CommentSerializer, TaskListSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404


class TasksView(generics.ListCreateAPIView):
    """
    Handles listing and creation of tasks.

    GET  /api/tasks/ → Returns all tasks visible to the current user (owner, assignee, or reviewer)
    POST /api/tasks/ → Creates a new task (requires board and user permissions)
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns all tasks where the current user is either:
        - the owner,
        - the assignee, or
        - the reviewer.
        """
        user = self.request.user
        return Task.objects.filter(
            Q(owner=user) | Q(assignee=user) | Q(reviewer=user)
        ).distinct()

    def perform_create(self, serializer):
        """
        Ensures only board members can create tasks.
        """
        user = self.request.user
        board = serializer.validated_data.get("board")

        if not board.members.filter(id=user.id).exists():
            raise PermissionDenied("You must be a member of this board to create a task.")

        serializer.save(owner=user)

    def create(self, request, *args, **kwargs):
        """
        Overrides the default create() method to return a TaskListSerializer
        after saving the task. This ensures the response includes
        `board` and `comments_count` fields.
        """
        response = super().create(request, *args, **kwargs)
        task = Task.objects.get(pk=response.data["id"])
        data = TaskListSerializer(task, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles retrieval, updates, and deletion of a single task.

    GET    /api/tasks/<task_id>/ → Retrieve a task if the user has access.
    PATCH  /api/tasks/<task_id>/ → Partially update task details.
    PUT    /api/tasks/<task_id>/ → Fully update task details.
    DELETE /api/tasks/<task_id>/ → Delete the task (if permitted).
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Retrieves the task by ID.
        Only the task's owner, assignee, or reviewer can access it.
        """
        task_id = self.kwargs.get("task_id")
        task = get_object_or_404(Task, pk=task_id)

        user = self.request.user
        if not (task.owner == user or task.assignee == user or task.reviewer == user):
            raise PermissionDenied("You are not allowed to view, edit, or delete this task.")

        return task

    def patch(self, request, *args, **kwargs):
        """Handles partial updates (PATCH) for a task."""
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """Handles full updates (PUT) for a task."""
        return self.update(request, *args, **kwargs)


class TaskCommentsView(generics.ListCreateAPIView):
    """
    Manages comments related to a specific task.

    GET  /api/tasks/<task_id>/comments/ → List all comments for a task.
    POST /api/tasks/<task_id>/comments/ → Add a new comment to a task.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_task(self):
        """Helper method to fetch the task instance for the given task_id."""
        task_id = self.kwargs.get("task_id")
        task = get_object_or_404(Task, pk=task_id)
        return task

    def get_queryset(self):
        """
        Returns all comments associated with the task,
        if the user has permission to view the task.
        """
        task = self.get_task()
        user = self.request.user

        if not (task.owner == user or task.assignee == user or task.reviewer == user):
            raise PermissionDenied("You are not allowed to view comments for this task.")

        queryset = Comment.objects.filter(task=task).order_by("created_at")

        if not queryset.exists():
            raise NotFound("No comments found for this task.")

        return queryset

    def perform_create(self, serializer):
        """
        Creates a new comment for a task.
        Only accessible to the owner, assignee, or reviewer.
        """
        task = self.get_task()
        user = self.request.user

        if not (task.owner == user or task.assignee == user or task.reviewer == user):
            raise PermissionDenied("You are not allowed to add comments to this task.")

        content = self.request.data.get("content")
        if not content or not content.strip():
            raise ValidationError({"content": "Comment content cannot be empty."})

        serializer.save(author=user, task=task)


class TaskCommentDetailView(generics.DestroyAPIView):
    """
    Handles deletion of individual comments.

    DELETE /api/tasks/<task_id>/comments/<comment_id>/ → Delete a comment if allowed.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Retrieves the comment by ID.
        Only the author or the board owner may delete a comment.
        """
        task_id = self.kwargs["task_id"]
        comment_id = self.kwargs["comment_id"]

        task = get_object_or_404(Task, pk=task_id)
        comment = get_object_or_404(Comment, pk=comment_id, task=task)

        user = self.request.user
        if not (comment.author == user or task.owner == user):
            raise PermissionDenied("You are not allowed to delete this comment.")

        return comment

    def delete(self, request, *args, **kwargs):
        """Deletes a comment and returns HTTP 204 on success."""
        comment = self.get_object()
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TasksAssignedToMeView(generics.ListAPIView):
    """
    GET /api/tasks/assigned-to-me/
    Returns all tasks that are assigned to the currently authenticated user.
    """
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Fetches all tasks assigned to the logged-in user.
        Orders results by due date.
        """
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
    Returns all tasks where the logged-in user is assigned as the reviewer.
    """
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Fetches all tasks where the current user is the reviewer.
        Orders results by due date.
        """
        user = self.request.user
        return (
            Task.objects
            .filter(reviewer=user)
            .select_related("board", "assignee", "reviewer")
            .order_by("due_date")
        )
