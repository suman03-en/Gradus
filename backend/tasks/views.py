from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Task, TaskSubmission
from .serializers import (
    TaskSerializer,
    TaskSubmissionSerializer
)
from .constants import TaskStatus
from accounts.permissions import IsTeacherOrReadOnly, IsStudentOrReadOnly
from .permissions import IsTaskCreatorOrClassroomStudent, CanViewTaskSubmission
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
            classroom=classroom,
            status=TaskStatus.PUBLISHED
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
    
class TaskRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskCreatorOrClassroomStudent]
    lookup_field = "id"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        if user.is_student:
            return Task.objects.filter(
                classroom__students=user
            )
        return Task.objects.filter(created_by=self.request.user)


class TaskSubmissionListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TaskSubmissionSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = (permissions.IsAuthenticated, IsStudentOrReadOnly, CanViewTaskSubmission)
    lookup_field = "id"
    lookup_url_kwarg = "uuid"

    def get_task(self):
        #returns the current task , using task_id from url path
        task_id = self.kwargs["uuid"]
        task = generics.get_object_or_404(
            Task,
            id=task_id            
        )
        return task
    
    def get_queryset(self):
        if self.request.user.is_student:
            return TaskSubmission.objects.filter(task=self.get_task(), student=self.request.user)
        return TaskSubmission.objects.filter(task=self.get_task(), task__created_by=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        task = self.get_task()
        context["task"]=task
        context["user"] = self.request.user
        return context
    


