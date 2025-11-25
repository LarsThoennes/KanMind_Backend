from rest_framework import serializers
from ..models import Task, Comment
from boards_app.models import Board
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

User = get_user_model()


class BoardPrimaryKeyField(serializers.PrimaryKeyRelatedField):
    """
    Custom field for validating Board primary keys.
    Raises a 404 error if the provided Board ID does not exist.
    """
    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError:
            raise NotFound("Board not found. The provided Board ID does not exist.")


class UserCompactSerializer(serializers.ModelSerializer):
    """
    Compact serializer for user data used inside task responses.
    Returns only ID, email, and username (as fullname).
    """
    fullname = serializers.CharField(source="username", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class TaskSerializer(serializers.ModelSerializer):
    """
    Main Task serializer.
    Used for creating and updating tasks.
    The board field is only required on POST requests (write-only).
    """
    board = BoardPrimaryKeyField(queryset=Board.objects.all(), required=False, write_only=True)

    assignee = UserCompactSerializer(read_only=True)
    reviewer = UserCompactSerializer(read_only=True)

    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="assignee",
        write_only=True,
        required=False,
        allow_null=True,
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="reviewer",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "assignee_id",
            "reviewer_id",
            "due_date",
            "board",
        ]
        read_only_fields = ["id", "assignee", "reviewer"]

    def validate(self, attrs):
        """
        Validation logic for Task creation and updates.

        - The board is required on POST but optional on PATCH/PUT.
        - The user must be either a member or owner of the board.
        - Assignee and reviewer must also be members of the same board.
        """
        request = self.context.get("request")
        method = request.method if request else None

        board = attrs.get("board") or getattr(self.instance, "board", None)
        assignee = attrs.get("assignee")
        reviewer = attrs.get("reviewer")
        owner = request.user if request else None

        if method == "POST" and not board:
            raise ValidationError({"board": "A board must be provided when creating a task."})

        if board and not (board.owner == owner or board.members.filter(id=owner.id).exists()):
            raise PermissionDenied({"board": "You are not a member or owner of this board."})

        if assignee and not board.members.filter(id=assignee.id).exists():
            raise PermissionDenied({"assignee_id": "Assignee must be a member of this board."})

        if reviewer and not board.members.filter(id=reviewer.id).exists():
            raise PermissionDenied({"reviewer_id": "Reviewer must be a member of this board."})

        return attrs


class TaskCompactSerializer(serializers.ModelSerializer):
    """
    A lightweight version of the Task serializer.
    Used for embedding tasks inside other objects (e.g., BoardDetailSerializer).
    """
    assignee = UserCompactSerializer(read_only=True)
    reviewer = UserCompactSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]
        read_only_fields = fields

    def get_comments_count(self, obj):
        """
        Returns the number of comments associated with this task.
        """
        return 0


class TaskListSerializer(serializers.ModelSerializer):
    """
    Serializer used for list endpoints such as:
    - /api/tasks/assigned-to-me/
    - /api/tasks/reviewing/

    Includes board as an ID and counts comments dynamically.
    """
    assignee = UserCompactSerializer(read_only=True)
    reviewer = UserCompactSerializer(read_only=True)
    board = serializers.PrimaryKeyRelatedField(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]
        read_only_fields = fields

    def get_comments_count(self, obj):
        """
        Returns the number of comments for the task.
        If the related name 'comments' exists on the Task model,
        it counts dynamically, otherwise returns 0.
        """
        return obj.comments.count() if hasattr(obj, "comments") else 0


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for handling comment data related to tasks.
    Returns author information and basic comment details.
    """
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]
        read_only_fields = ["id", "author", "created_at"]

    def get_author(self, obj):
        """
        Returns a string representing the comment author.
        Prefers full_name, then username, and finally email.
        """
        if hasattr(obj.author, "get_full_name") and obj.author.get_full_name():
            return obj.author.get_full_name()
        return obj.author.username or obj.author.email
