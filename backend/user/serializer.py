from rest_framework.serializers import ModelSerializer
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