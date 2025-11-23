from rest_framework import serializers
from ..models import Task, Comment
from boards_app.models import Board
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, PermissionDenied


User = get_user_model()

class BoardPrimaryKeyField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError:
            raise NotFound("Board nicht gefunden. Die angegebene Board-ID existiert nicht.")

class UserCompactSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(source="username", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class TaskSerializer(serializers.ModelSerializer):
    board = BoardPrimaryKeyField(queryset=Board.objects.all())
    assignee = UserCompactSerializer(read_only=True)
    reviewer = UserCompactSerializer(read_only=True)

    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="assignee",
        write_only=True,
        required=True,
        allow_null=True,
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="reviewer",
        write_only=True,
        required=True,
        allow_null=True,
    )

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
            "assignee_id",
            "reviewer_id",
            "due_date",
            "comments_count",
        ]
        read_only_fields = ["id", "assignee", "reviewer", "comments_count"]

    def validate(self, attrs):
        board = attrs.get("board")
        assignee = attrs.get("assignee")
        reviewer = attrs.get("reviewer")
        owner = self.context["request"].user  

        if not board.members.filter(id=owner.id).exists() and board.owner != owner:
            raise PermissionDenied(
                {"board": f"Du bist kein Mitglied oder Owner des Boards {board.id}."}
            )

        if assignee and not board.members.filter(id=assignee.id).exists():
            raise PermissionDenied(
                {"assignee_id": f"User {assignee.id} ist kein Mitglied des Boards {board.id}."}
            )

        if reviewer and not board.members.filter(id=reviewer.id).exists():
            raise PermissionDenied(
                {"reviewer_id": f"User {reviewer.id} ist kein Mitglied des Boards {board.id}."}
            )

        return attrs

    def get_comments_count(self, obj):
        return 0
    
class TaskCompactSerializer(serializers.ModelSerializer):
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
        return 0

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]
        read_only_fields = ["id", "author", "created_at"]

    def get_author(self, obj):
        if hasattr(obj.author, "get_full_name") and obj.author.get_full_name():
            return obj.author.get_full_name()
        return obj.author.username or obj.author.email