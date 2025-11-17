from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, get_user_model

class RegistrationSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(write_only=True) 
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'Email is already in use.'})

        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})

        return data

    def create(self, validated_data):
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
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            try:
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("keinen Benutzer mit dieser Email gefunden")

            user = authenticate(username=user_obj.username, password=password)
            if not user:
                raise serializers.ValidationError("Der gefunde Username kann nicht authentifiziert werden")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'")

        attrs["user"] = user
        return attrs

