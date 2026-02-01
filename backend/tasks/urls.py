from django.urls import path
from .views import TaskRetrieveUpdateDestroyAPIView, TaskSubmissionAPIView

urlpatterns = [
    path("<uuid:uuid>/", TaskRetrieveUpdateDestroyAPIView.as_view()),
    path("<uuid:uuid>/submit/", TaskSubmissionAPIView.as_view()),
]
