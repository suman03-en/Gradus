from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes as perm_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import update_last_login

from accounts.views import LoginView


class TokenLoginAPIView(LoginView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (AllowAny,)

    def login(self):
        self.user = self.serializer.validated_data["user"]
        update_last_login(None, self.user)
        self.token, _ = Token.objects.get_or_create(user=self.user)


class TokenLogoutAPIView(APIView):
    """
    For token authentication, delete the token.
    """

    authentication_classes = (TokenAuthentication,)

    def post(self, request, *args, **kwargs):
        return self.logout(request)

    def logout(self, request):

        request.user.auth_token.delete()

        response = Response(
            {"detail": "Successfully logout."}, status=status.HTTP_200_OK
        )

        return response


@api_view(["GET"])
@perm_classes([AllowAny])
def api_root(request, format=None):
    return Response(
        {
            "accounts": {
                "register": request.build_absolute_uri("accounts/register/"),
                "login": request.build_absolute_uri("accounts/login/"),
                "logout": request.build_absolute_uri("accounts/logout/"),
                "me": request.build_absolute_uri("accounts/users/me"),
                "profile": request.build_absolute_uri("accounts/profile/me"),
                "password-reset-request": request.build_absolute_uri(
                    "accounts/password-reset/request/"
                ),
                "password-reset-verify": request.build_absolute_uri(
                    "accounts/password-reset/verify/"
                ),
                "password-reset-confirm": request.build_absolute_uri(
                    "accounts/password-reset/confirm/"
                ),
            },
            "auth-token": {
                "login": request.build_absolute_uri("auth-token/login/"),
                "logout": request.build_absolute_uri("auth-token/logout/"),
            },
            "classrooms": {
                "list-create": request.build_absolute_uri("classrooms/"),
                "join": request.build_absolute_uri("classrooms/join/"),
                "detail": request.build_absolute_uri("classrooms/<uuid>/"),
                "students": request.build_absolute_uri("classrooms/<uuid>/students/"),
                "gradebook": request.build_absolute_uri("classrooms/<uuid>/gradebook/"),
                "gradebook-weightages": request.build_absolute_uri(
                    "classrooms/<uuid>/gradebook/weightages/"
                ),
                "tasks": request.build_absolute_uri("classrooms/<uuid>/tasks/"),
            },
            "tasks": {
                "detail": request.build_absolute_uri("tasks/<uuid>/"),
                "submit": request.build_absolute_uri("tasks/<uuid>/submit/"),
                "bulk-evaluate": request.build_absolute_uri(
                    "tasks/<uuid>/bulk-evaluate/"
                ),
                "evaluate-student": request.build_absolute_uri(
                    "tasks/<uuid>/evaluate-student/<roll_no>/"
                ),
                "record-update": request.build_absolute_uri(
                    "tasks/records/<uuid>/update"
                ),
                "record-evaluate": request.build_absolute_uri(
                    "tasks/records/<uuid>/evaluate/"
                ),
                "record-detail": request.build_absolute_uri("tasks/records/<uuid>/"),
            },
            "resources": request.build_absolute_uri("resources/"),
        }
    )
