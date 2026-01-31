from django.shortcuts import get_object_or_404

from rest_framework import generics
from .models import Task
from .serializers import TaskSerializer
from accounts.permissions import IsTeacherOrNotAllowed
from classrooms.models import Classroom

class TaskCreateAPIView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsTeacherOrNotAllowed, )


    def get_serializer_context(self):
        context = super().get_serializer_context()

        classroom_id = self.kwargs["uuid"]
        classroom = get_object_or_404(
            Classroom,
            id=classroom_id,
            is_active=True
        )
        context["user"] = self.request.user
        context["classroom"] = classroom
        
        return context
