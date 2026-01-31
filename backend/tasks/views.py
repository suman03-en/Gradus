from django.shortcuts import get_object_or_404

from rest_framework import generics
from .models import Task
from .serializers import TaskSerializer
from classrooms.permissions import IsTeacherOrReadOnly
from classrooms.models import Classroom

class TaskListCreateAPIView(generics.ListCreateAPIView):
    """
    Ability to list and create for teachers.
    Ability to list only for students.
    """
    serializer_class = TaskSerializer
    permission_classes = (IsTeacherOrReadOnly, )

    def get_queryset(self):
        classroom = self.get_classroom()
        queryset = Task.objects.filter(
            classroom=classroom
        )
        return queryset

    def get_classroom(self):
        classroom_id = self.kwargs["uuid"]
        classroom = get_object_or_404(
            Classroom,
            id=classroom_id,
            is_active=True
        )
        return classroom
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        context["classroom"] = self.get_classroom()
        return context
    

