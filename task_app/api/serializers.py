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
        owner = self.context["request"].user  # eingeloggter User

        # 1. Prüfen, ob Owner überhaupt Mitglied des Boards ist
        if not board.members.filter(id=owner.id).exists() and board.owner != owner:
            raise PermissionDenied(
                {"board": f"Du bist kein Mitglied oder Owner des Boards {board.id}."}
            )

        # 2. Prüfen, ob Assignee im Board ist
        if assignee and not board.members.filter(id=assignee.id).exists():
            raise PermissionDenied(
                {"assignee_id": f"User {assignee.id} ist kein Mitglied des Boards {board.id}."}
            )

        # 3. Prüfen, ob Reviewer im Board ist
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
        read_only_fields = fields  # Alles read-only für Board-Detail

    def get_comments_count(self, obj):
        return 0

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]
        read_only_fields = ["id", "author", "created_at"]

    def get_author(self, obj):
        # Wenn du den vollständigen Namen hast:
        if hasattr(obj.author, "get_full_name") and obj.author.get_full_name():
            return obj.author.get_full_name()
        # Fallback: username oder email
        return obj.author.username or obj.author.email

# serializer mit Kommentaren 


# from rest_framework import serializers
# from ..models import Task
# from django.contrib.auth import get_user_model

# User = get_user_model()

# class UserCompactSerializer(serializers.ModelSerializer):
#     # Wandelt username in fullname um damit es im response richtig dargestellt wird.
#     fullname = serializers.CharField(source="username", read_only=True)

#     class Meta:
#         model = User
#         # Der Response dieses Serializers enthält diese 3 Felder des User-Modells
#         fields = ["id", "email", "fullname"]


# class TaskSerializer(serializers.ModelSerializer):
#     # Holt sich für den assignee und reviewer jeweils die id, email und fullname
#     assignee = UserCompactSerializer(read_only=True)
#     reviewer = UserCompactSerializer(read_only=True)

#    # Wird nur im Request (z. B. POST) berücksichtigt
#     assignee_id = serializers.PrimaryKeyRelatedField(
#         # Sucht in User nach einen passenden user mit der id
#         queryset=User.objects.all(),
#         source="assignee",# in validated_data heisst es assignee und nicht assignee_id
#         write_only=True,# Tauscht nicht im response auf
#         required=True, # Client muss das Feld mitschicken, auch wenn es null ist
#         allow_null=True, # Kann null sein
#     )
#      # Wird nur beim POST berücksichtigt, da es vom User mitgeschickt werden muss
#     reviewer_id = serializers.PrimaryKeyRelatedField(
#         queryset=User.objects.all(),
#         source="reviewer",
#         write_only=True,
#         required=True,
#         allow_null=True,
#     )

#     # Extra feld, kein Model-Feld
#     comments_count = serializers.SerializerMethodField() # Es sagt das es kein feld aus dem Model ist sondern eine Methode im Serializer, dann sucht DRf automatischt nach einer methode get_Feldname

#     class Meta:
#         # Der Serializer orientiert sich am Task aus models.py
#         model = Task
#         # Gibt an welche felder im request und response erscheinen sollen
#         fields = [
#             "id",
#             "board",
#             "title",
#             "description",
#             "status",
#             "priority",
#             "assignee",     # Response: Nested User
#             "reviewer",     # Response: Nested User
#             "assignee_id",  # Request: ID
#             "reviewer_id",  # Request: ID
#             "due_date",
#             "comments_count",
#         ]
#         # Dürfen nicht vom User gesetzt werden und erscheinen nur im response und NICHT im Request
#         read_only_fields = ["id", "assignee", "reviewer", "comments_count"]

#     def get_comments_count(self, obj):
#         # später kannst du hier obj.comments.count() nutzen
#         return 0

