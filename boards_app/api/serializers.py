from rest_framework import serializers
from boards_app.models import Board
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound
from task_app.api.serializers import TaskCompactSerializer

User = get_user_model()

class BoardSerializer(serializers.ModelSerializer):
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
        read_only_fields = ["id", "member_count", "ticket_count", "tasks_to_do_count", "tasks_high_prio_count", "owner_id"]

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        board = Board.objects.create(**validated_data) 
        board.members.set(members)
        return board


    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        return 0

    def get_tasks_to_do_count(self, obj):
        return 0

    def get_tasks_high_prio_count(self, obj):
        return 0
    

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


class BoardDetailSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)
    members = UserCompactSerializer(many=True, read_only=True)
    tasks = TaskCompactSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "owner_id",
            "members",
            "tasks"
        ]
        read_only_fields = fields