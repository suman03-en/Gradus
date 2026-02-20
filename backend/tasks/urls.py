from django.urls import path
from .views import (
    TaskRetrieveUpdateDestroyAPIView,
    TaskSubmissionListCreateAPIView,
    TaskEvaluationAPIView,
    TaskEvaluationDetailAPIView
)

urlpatterns = [
    path("<uuid:uuid>/", TaskRetrieveUpdateDestroyAPIView.as_view()),
    path("<uuid:uuid>/submit/", TaskSubmissionListCreateAPIView.as_view()),
    path("submissions/<uuid:submission_id>/evaluate/", TaskEvaluationAPIView.as_view()),
    path("submissions/<uuid:submission_id>/", TaskEvaluationDetailAPIView.as_view()),
]
