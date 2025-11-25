from django.db.models import Q
from rest_framework import generics
from boards_app.models import Board
from .serializers import (
    BoardSerializer,
    BoardDetailSerializer,
    BoardDetailWithOwnerSerializer,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response


class BoardsView(generics.ListCreateAPIView):
    """
    Handles board listing and creation.

    GET  /api/boards/ → Returns all boards where the current user is either the owner or a member.
    POST /api/boards/ → Creates a new board with the authenticated user as the owner.
    """
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns all boards accessible to the logged-in user
        (either as the owner or as a member).
        """
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        """
        Assigns the authenticated user as the board owner when creating a new board.
        """
        serializer.save(owner=self.request.user)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, and deleting a single board.

    GET    /api/boards/<board_id>/ → Returns the board if the user has access.
    PATCH  /api/boards/<board_id>/ → Updates the board (owner only).
    PUT    /api/boards/<board_id>/ → Fully updates the board (owner only).
    DELETE /api/boards/<board_id>/ → Deletes the board (owner only).
    """
    serializer_class = BoardDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns only boards that the current user is allowed to access.
        This includes boards where the user is either the owner or a member.
        """
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def get_serializer_class(self):
        """
        Uses a more detailed serializer when performing updates
        to include full owner and member data in the response.
        """
        if self.request.method in ["PATCH", "PUT"]:
            return BoardDetailWithOwnerSerializer
        return BoardDetailSerializer

    def get_object(self):
        """
        Retrieves the board instance from the filtered queryset.
        Converts unauthorized access into a 403 Forbidden error.
        """
        try:
            board = super().get_object()
        except Exception:
            raise PermissionDenied("You are not allowed to view or modify this board.")

        # Only the board owner can modify or delete the board
        if self.request.method in ["PATCH", "PUT", "DELETE"] and board.owner != self.request.user:
            raise PermissionDenied("Only the board owner can modify or delete this board.")

        return board

    def perform_destroy(self, instance):
        """
        Deletes the board if the authenticated user is the owner.
        """
        user = self.request.user
        if instance.owner != user:
            raise PermissionDenied("Only the board owner can delete this board.")
        instance.delete()


class EmailCheckView(APIView):
    """
    Simple endpoint to verify authentication and return
    the logged-in user's basic information.

    GET /api/boards/email-check/ → Returns user ID, email, and fullname.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns basic profile information for the currently authenticated user.
        """
        user = request.user
        return Response({
            "id": user.id,
            "email": user.email,
            "fullname": user.username,
        })
