from django.urls import path
from .views import (
    RegisterUserAPIView, 
    LoginView, 
    LogoutView, 
    UserDetailsView, 
    UserProfileDetailsView,
    PasswordResetEmailView,
    VerifyOTPView,
    ResetPasswordView,
    ProfileRetrieveUpdateView,
)


urlpatterns = [
    path("register/",RegisterUserAPIView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path('password-reset/request/', PasswordResetEmailView.as_view(), name='request-password-reset'),
    path('password-reset/verify/', VerifyOTPView.as_view(), name='verify-otp'),
    path('password-reset/confirm/', ResetPasswordView.as_view(), name='reset-password'),
    path("users/me", UserDetailsView.as_view()),
    path("users/<str:username>", UserProfileDetailsView.as_view(), name="user-detail"),
    path("profile/me", ProfileRetrieveUpdateView.as_view()),
]
