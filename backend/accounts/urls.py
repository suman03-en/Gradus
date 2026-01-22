from django.urls import path
from .views import RegisterUserAPIView, LoginView, LogoutView

urlpatterns = [
    path("register/",RegisterUserAPIView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
]
