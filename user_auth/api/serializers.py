from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, get_user_model


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Handles user registration and validation.

    Fields:
    - fullname: User's display name (mapped to username)
    - email: User's unique email address
    - password: Chosen password
    - repeated_password: Confirmation of the chosen password

    Ensures:
    - Email is unique
    - Passwords match
    """
    fullname = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        """
        Validates registration data.
        - Checks if email is already taken.
        - Ensures that both passwords match.
        """
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'Email is already in use.'})

        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})

        return data

    def create(self, validated_data):
        """
        Creates a new user account with the provided credentials.
        The 'fullname' field is mapped to the Django 'username' field.
        """
        validated_data.pop('repeated_password')
        fullname = validated_data.pop('fullname')

        account = User(
            email=validated_data['email'],
            username=fullname
        )
        account.set_password(validated_data['password'])
        account.save()
        return account


User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """
    Handles user login via email and password authentication.

    Fields:
    - email: The user's registered email address
    - password: The user's password

    Returns the authenticated user instance upon successful validation.
    """
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        """
        Validates the provided credentials.
        - Confirms the email exists.
        - Authenticates the user using Django's authentication system.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            try:
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this email address.")

            user = authenticate(username=user_obj.username, password=password)
            if not user:
                raise serializers.ValidationError("The provided password is incorrect.")
        else:
            raise serializers.ValidationError("Both 'email' and 'password' are required.")

        attrs["user"] = user
        return attrs
