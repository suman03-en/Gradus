from django.urls import path
from .views import TaskRetrieveUpdateDestroyAPIView

urlpatterns = [
    path("<uuid:uuid>/", TaskRetrieveUpdateDestroyAPIView.as_view()),
]
