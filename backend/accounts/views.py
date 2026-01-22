from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from django.contrib.auth import (
    login as django_login,
    logout as django_logout,
)
from django.conf import settings
from django.contrib.auth import get_user_model

from .serializers import UserSerializer, LoginSerializer

UserModel = get_user_model()

class RegisterUserAPIView(generics.CreateAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer


class LoginView(generics.GenericAPIView):
    """
    Calls Django Auth login method to register User ID
    in Django session framework

    Accept the following POST parameters: username, password
    """
    permission_classes = (AllowAny, )
    serializer_class = LoginSerializer

    def process_login(self):
        django_login(self.request, self.user)

    def login(self):
        self.user = self.serializer.validated_data['user']

        if getattr(settings, 'REST_SESSION_LOGIN', True):
            self.process_login()

    def post(self, request, *args, **kwargs):
        self.request = request
        self.serializer = self.get_serializer(
            data=self.request.data, 
            context={'request':self.request}
            )
        self.serializer.is_valid(raise_exception=True)
        self.login()

        response = Response({"details": "Successfully logged in."}, status=status.HTTP_200_OK)
        
        return response

        
class LogoutView(APIView):
    """
    Calls Django logout method

    Accepts/Returns nothing.
    """
    permission_classes = (IsAuthenticated, )

        
    def post(self, request, *args, **kwargs):
        return self.logout(request)
    
    def logout(self, request):
        """
        For token authentication, delete the token .
        and for session, call the django logout method.
        """
        if getattr(settings, 'REST_SESSION_LOGIN', True):
            django_logout(request)

        response = Response({"details": "Successfully logout."}, status=status.HTTP_200_OK)

        return response