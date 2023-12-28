from rest_framework import serializers
from django.contrib.auth.models import Permission
from .models import AuthUser


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuthUser
        fields = ["id", "email", "username", "password"]

    def create(self, validated_data):
        user = AuthUser.objects.create(email=validated_data['email'],
                                       username=validated_data['username']
                                         )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    
    # user_permissions = serializers.SlugRelatedField(
    #     many=True, queryset=Permission.objects.all(), slug_field="id"
    # )

    class Meta:
        model = AuthUser
        fields = ['id', 'username', 'feature_perms']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)