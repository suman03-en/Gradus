from django.urls import path
from .views import (
    TaskRetrieveUpdateDestroyAPIView,
    TaskRecordListCreateAPIView,
    TaskRecordUpdateAPIView,
    TaskRecordEvaluationAPIView,
    TaskStudentEvaluationAPIView,
    TaskRecordDetailAPIView,
    BulkTaskEvaluationAPIView
)

urlpatterns = [
    path("<uuid:uuid>/", TaskRetrieveUpdateDestroyAPIView.as_view()),
    path("<uuid:uuid>/submit/", TaskRecordListCreateAPIView.as_view()),
    path("records/<uuid:record_id>/update", TaskRecordUpdateAPIView.as_view()),
    path("<uuid:task_id>/bulk-evaluate/", BulkTaskEvaluationAPIView.as_view()),
    path("<uuid:task_id>/evaluate-student/<str:roll_no>/", TaskStudentEvaluationAPIView.as_view()),
    path("records/<uuid:record_id>/evaluate/", TaskRecordEvaluationAPIView.as_view()),
    path("records/<uuid:record_id>/", TaskRecordDetailAPIView.as_view()),
]
