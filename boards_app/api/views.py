from django.db.models import Q
from rest_framework import generics
from boards_app.models import Board
from .serializers import BoardSerializer, BoardDetailSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response

class BoardsView(generics.ListCreateAPIView):
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Board.objects.all()
    serializer_class = BoardDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        board = super().get_object()
        user = self.request.user
        if board.owner != user and not board.members.filter(id=user.id).exists():
            raise PermissionDenied("Du darfst dieses Board nicht ansehen oder bearbeiten.")
        return board

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.owner != user:
            raise PermissionDenied("Nur der Besitzer darf dieses Board löschen.")
        instance.delete()

class EmailCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "email": user.email,
            "fullname": user.username,  # falls du full_name hast: user.get_full_name() or user.full_name
        })