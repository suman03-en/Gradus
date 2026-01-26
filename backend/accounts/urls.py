from django.urls import path
from .views import (
    RegisterUserAPIView, 
    LoginView, 
    LogoutView, 
    UserDetailsView, 
    ProfileRetrieveUpdateView
)

urlpatterns = [
    path("register/",RegisterUserAPIView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("users/me", UserDetailsView.as_view()),
    path("profile/me", ProfileRetrieveUpdateView.as_view()),
]
