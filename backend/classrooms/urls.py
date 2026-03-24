from django.urls import path, include
from .views import (
    ClassroomListCreateView,
    ClassroomJoinView,
    ClassroomDetailView,
    ClassroomGradebookAPIView,
    ClassroomGradebookExcelExportAPIView,
    ClassroomAddStudentView,
    ClassroomAddTeacherView,
    ClassroomWeightageConfigAPIView,
)
from tasks.views import TaskListCreateAPIView

urlpatterns = [
    path("", ClassroomListCreateView.as_view()),
    path("join/", ClassroomJoinView.as_view()),
    path("<uuid:uuid>/students/", ClassroomAddStudentView.as_view()),
    path("<uuid:uuid>/teachers/", ClassroomAddTeacherView.as_view()),
    path("<uuid:uuid>/", ClassroomDetailView.as_view()),
    path("<uuid:uuid>/gradebook/", ClassroomGradebookAPIView.as_view()),
    path(
        "<uuid:uuid>/gradebook/export-excel/",
        ClassroomGradebookExcelExportAPIView.as_view(),
    ),
    path(
        "<uuid:uuid>/gradebook/weightages/", ClassroomWeightageConfigAPIView.as_view()
    ),
    path("<uuid:uuid>/tasks/", TaskListCreateAPIView.as_view()),
]
