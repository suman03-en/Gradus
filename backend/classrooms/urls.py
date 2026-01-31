from django.urls import path, include
from .views import (
    ClassroomListCreateView, 
    ClassroomJoinView, 
    ClassroomDetailView, 
    ClassroomAddStudentView,
)
from tasks.views import TaskCreateAPIView

urlpatterns = [
    path("", ClassroomListCreateView.as_view()),
    path("join/", ClassroomJoinView.as_view()),
    path("<uuid:uuid>/students/", ClassroomAddStudentView.as_view()),
    path("<uuid:uuid>/", ClassroomDetailView.as_view()),
    path("<uuid:uuid>/tasks/", TaskCreateAPIView.as_view()),
]
