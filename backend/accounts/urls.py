from django.urls import path
from .views import (
    RegisterUserAPIView, 
    LoginView, 
    LogoutView, 
    UserDetailsView, 
    ProfileRetrieveUpdateView
)

urlpatterns = [
    path("auth/register/",RegisterUserAPIView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("users/me", UserDetailsView.as_view()),
    path("profile/me", ProfileRetrieveUpdateView.as_view()),
]
