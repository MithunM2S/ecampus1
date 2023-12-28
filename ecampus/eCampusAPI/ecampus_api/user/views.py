from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import *
from rest_framework.response import Response
from .models import AuthUser
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny


# view for registering users
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

#for updating and listing
class UserViewSet(viewsets.ModelViewSet):
    queryset = AuthUser.objects.filter(is_staff=False, is_active=True)
    serializer_class = UserSerializer

class ChangePasswordView(APIView):
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        user = AuthUser.objects.get(id=request.data['user'])

        if serializer.is_valid():
            old_password = serializer.data.get('old_password')
            new_password = serializer.data.get('new_password')

            if not user.check_password(old_password) and not request.user.is_superuser:
                return Response({'detail': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({'detail': 'Password has been changed.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
