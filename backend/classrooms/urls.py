from django.urls import path, include
from .views import ClassroomListCreateView

urlpatterns = [
    path("", ClassroomListCreateView.as_view()),

]
