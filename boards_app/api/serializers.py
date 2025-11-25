from rest_framework import serializers
from boards_app.models import Board
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound
from task_app.api.serializers import TaskCompactSerializer

User = get_user_model()


class BoardSerializer(serializers.ModelSerializer):
    """
    Serializer for listing and creating boards.

    Includes metadata such as:
    - member count
    - total task count
    - number of 'to-do' tasks
    - number of high priority tasks
    """
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)

    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        write_only=True
    )

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "members",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]
        read_only_fields = [
            "id",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]

    def create(self, validated_data):
        """
        Creates a new board and assigns its members.
        """
        members = validated_data.pop("members", [])
        board = Board.objects.create(**validated_data)
        board.members.set(members)
        return board

    def get_member_count(self, obj):
        """
        Returns the number of members associated with the board.
        """
        return obj.members.count()

    def get_ticket_count(self, obj):
        """
        Returns the total number of tasks linked to this board.
        """
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """
        Returns the number of tasks in this board with status 'to-do'.
        """
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        """
        Returns the number of tasks in this board with priority 'high'.
        """
        return obj.tasks.filter(priority="high").count()


class BoardPrimaryKeyField(serializers.PrimaryKeyRelatedField):
    """
    Custom PrimaryKeyRelatedField for Boards.
    Raises a 404 (NotFound) if the provided Board ID does not exist.
    """
    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError:
            raise NotFound("Board not found. The provided Board ID does not exist.")


class UserCompactSerializer(serializers.ModelSerializer):
    """
    Compact serializer for user representation within board responses.
    Includes ID, email, and username as 'fullname'.
    """
    fullname = serializers.CharField(source="username", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single board.

    Includes:
    - owner ID
    - member details
    - editable member IDs
    - associated tasks
    """
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)
    members = UserCompactSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=User.objects.all(),
        required=False,
        source="members",
    )
    tasks = TaskCompactSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "owner_id",
            "members",
            "member_ids",
            "tasks",
        ]
        read_only_fields = ["id", "owner_id", "members", "tasks"]

    def update(self, instance, validated_data):
        """
        Updates board data and synchronizes member relationships if provided.
        """
        members = validated_data.pop("members", None)
        instance = super().update(instance, validated_data)
        if members is not None:
            instance.members.set(members)
        return instance


class BoardDetailWithOwnerSerializer(BoardDetailSerializer):
    """
    Extended board detail serializer including full owner and member details.

    Used for endpoints that require richer data (e.g., PATCH/PUT views).
    """
    owner_data = UserCompactSerializer(source="owner", read_only=True)
    members_data = UserCompactSerializer(source="members", many=True, read_only=True)

    class Meta(BoardDetailSerializer.Meta):
        fields = [
            "id",
            "title",
            "owner_data",
            "members_data",
            "member_ids",
        ]
