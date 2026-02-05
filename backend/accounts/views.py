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
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication

from .models import (
    StudentProfile,
)
from .serializers import (
    UserSerializer, 
    LoginSerializer, 
    UserDetailsSerializer, 
    StudentProfileSerializer,
    TeacherProfileSerializer
)


UserModel = get_user_model()

class RegisterUserAPIView(generics.CreateAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny, )


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
        self.token = None

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
        
        data = {
            "detail": "Successfully logged in."
        }

        if self.token:
            data["token"] = self.token.key

        response = Response(data, status=status.HTTP_200_OK)
        
        return response

        
class LogoutView(APIView):
    """
        For session authentication, call django logout.
    """
    permission_classes = (IsAuthenticated, )

        
    def post(self, request, *args, **kwargs):
        return self.logout(request)
    
    def logout(self, request):

        if getattr(settings, 'REST_SESSION_LOGIN', True):
            django_logout(request)

        response = Response({"detail": "Successfully logout."}, status=status.HTTP_200_OK)

        return response
    
 
class UserDetailsView(generics.RetrieveUpdateAPIView):
    """
    Reads and updates UserModel fields
    Accepts GET, PUT, PATCH methods.

    Default accepted fields: username, first_name, last_name
    Default display fields: pk, username, email, first_name, last_name
    Read-only fields: pk

    Returns UserModel fields.
    """
    queryset = UserModel.objects.all()
    serializer_class = UserDetailsSerializer
    permission_classes = (IsAuthenticated, )

    def get_object(self):
        return self.request.user

class UserProfileDetailsView(generics.RetrieveAPIView):
    """
    General class for just viewing the profile of any user[student, teachers]
    """
    queryset = UserModel.objects.all()
    serializer_class = UserDetailsSerializer
    lookup_field = "username"

class ProfileRetrieveUpdateView(generics.CreateAPIView, generics.RetrieveUpdateAPIView):
    queryset = StudentProfile.objects.all()
    permission_classes = (IsAuthenticated, )

    def _is_student(self, user):
        if user.is_student:
            return user.student_profile
        return user.teacher_profile
    
    def get_object(self):
        return self._is_student(self.request.user)
    
    def get_serializer_class(self):
        if self.request.user.is_student:
            return StudentProfileSerializer
        return TeacherProfileSerializer





