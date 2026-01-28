from django.urls import path, include
from .views import ClassroomListCreateView, ClassroomJoinView

urlpatterns = [
    path("", ClassroomListCreateView.as_view()),
    path("join/", ClassroomJoinView.as_view()),
]
