from rest_framework import generics, status
from .serializers import RegistrationSerializer, LoginSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

User = get_user_model()


class RegistrationView(APIView):
    """
    Handles user registration and token creation.

    POST /api/auth/register/
    - Validates and registers a new user account.
    - Returns an authentication token and basic user info upon success.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Creates a new user account with the provided credentials.
        If successful, returns an authentication token.
        """
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            saved_account = serializer.save()
            token, _ = Token.objects.get_or_create(user=saved_account)

            data = {
                "token": token.key,
                "fullname": saved_account.username,
                "email": saved_account.email,
                "user_id": saved_account.id,
            }
            return Response(data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(APIView):
    """
    Handles user authentication (login) using email and password.

    POST /api/auth/login/
    - Authenticates a user via email and password.
    - Returns an authentication token and basic user information.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Authenticates a user and returns an authentication token.
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            token, _ = Token.objects.get_or_create(user=user)

            data = {
                "token": token.key,
                "fullname": user.username,
                "email": user.email,
                "user_id": user.id,
            }
            return Response(data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailCheckView(APIView):
    """
    Validates whether an email address exists in the system.

    GET /api/auth/email-check/?email=<email>
    - Validates email format.
    - Checks if the email is registered in the system.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Validates and checks an email address.
        Returns user information if found, otherwise appropriate error messages.
        """
        email = request.query_params.get("email")

        if not email:
            return Response(
                {"detail": "Email address must be provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"detail": "Invalid email format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "The specified email was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = {
            "id": user.id,
            "email": user.email,
            "fullname": user.username,
        }
        return Response(data, status=status.HTTP_200_OK)