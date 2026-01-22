from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.contrib.auth import (
    login as django_login,
)
from django.contrib.auth.models import User
from django.conf import settings

from .serializers import UserSerializer, LoginSerializer
class RegisterUserAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class LoginView(generics.GenericAPIView):
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
        return Response({"success":True, "msg":"login successfull."}, status=status.HTTP_200_OK)

        

