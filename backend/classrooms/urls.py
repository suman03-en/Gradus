from django.urls import path, include
from .views import ClassroomListCreateView, ClassroomJoinView, ClassroomDetailView

urlpatterns = [
    path("", ClassroomListCreateView.as_view()),
    path("join/", ClassroomJoinView.as_view()),
    path("<str:id>/", ClassroomDetailView.as_view()),
]
