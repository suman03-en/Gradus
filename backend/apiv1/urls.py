from django.urls import path, include
from .views import TokenLoginAPIView, TokenLogoutAPIView


urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('classrooms/', include('classrooms.urls')),
]

urlpatterns += [
    path("auth-token/login/", TokenLoginAPIView.as_view()),
    path("auth-token/logout/", TokenLogoutAPIView.as_view()),
]
