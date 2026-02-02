from django.urls import path
from .views import TaskRetrieveUpdateDestroyAPIView, TaskSubmissionListCreateAPIView

urlpatterns = [
    path("<uuid:uuid>/", TaskRetrieveUpdateDestroyAPIView.as_view()),
    path("<uuid:uuid>/submit/", TaskSubmissionListCreateAPIView.as_view()),
]
