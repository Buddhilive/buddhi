from rest_framework.serializers import ModelSerializer, Serializer, EmailField, CharField, ValidationError
from django.contrib.auth import authenticate
from .models import UserProfile

class UserProfileSerializer(ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'email')

class RegisterUserSerializer(ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('email', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = UserProfile.objects.create_user(**validated_data)
        return user

class LoginUserSerializer(Serializer):
    email = EmailField(required=True)
    password = CharField(required=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise ValidationError("Invalid credentials or user is inactive.")