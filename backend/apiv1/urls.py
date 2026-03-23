from django.urls import path, include
from .views import TokenLoginAPIView, TokenLogoutAPIView, api_root


urlpatterns = [
    path('', api_root, name='api-root'),
    path('accounts/', include('accounts.urls')),
    path('classrooms/', include('classrooms.urls')),
    path('tasks/', include('tasks.urls')),
    path('resources/', include('resources.urls')),
]

#token authentication urlpatterns
urlpatterns += [
    path("auth-token/login/", TokenLoginAPIView.as_view()),
    path("auth-token/logout/", TokenLogoutAPIView.as_view()),
]

