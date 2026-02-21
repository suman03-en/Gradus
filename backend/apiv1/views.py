from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token

from accounts.views import LoginView


class TokenLoginAPIView(LoginView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (AllowAny, )
    
    def login(self):
        self.user = self.serializer.validated_data['user']
        self.token, _ = Token.objects.get_or_create(user=self.user)
    
class TokenLogoutAPIView(APIView):
    """
        For token authentication, delete the token.
    """
    authentication_classes = (TokenAuthentication, )

        
    def post(self, request, *args, **kwargs):
        return self.logout(request)
    
    def logout(self, request):

        request.user.auth_token.delete()

        response = Response({"detail": "Successfully logout."}, status=status.HTTP_200_OK)

        return response
 

class GradeBookAPIView(generics.GenericAPIView):
    """This view list all the grades obtained in the tasks per classroom"""
    
