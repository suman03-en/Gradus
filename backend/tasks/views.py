from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Task, TaskSubmission, TaskEvaluation
from .serializers import (
    TaskSerializer,
    TaskSubmissionSerializer,
    TaskEvaluationSerialzer
)
from .constants import TaskStatus
from accounts.permissions import IsTeacherOrReadOnly, IsStudentOrReadOnly, IsTeacherOrNotAllowed
from .permissions import IsTaskCreatorOrClassroomStudent, CanViewTaskSubmission, CanViewTaskEvaluation, IsTaskSubmissionCreator
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
  
    
class TaskSubmissionUpdateAPIView(generics.UpdateAPIView):
    queryset = TaskSubmission.objects.select_related("task", "student")
    serializer_class = TaskSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskSubmissionCreator ]
    lookup_field = 'id'
    lookup_url_kwarg = "submission_id"

    def get_queryset(self):
        return self.queryset.filter(student=self.request.user)
    
    def get_serializer_context(self):
        """Add task context for validation."""
        context = super().get_serializer_context()
        submission = self.get_object()
        context['task'] = submission.task
        context['user'] = self.request.user
        return context
    
    def update(self, request, *args, **kwargs):
        """
        Handle PUT and PATCH requests with proper error handling.

        """ 
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "An error occurred while updating the submission."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    

    
class TaskEvaluationAPIView(generics.CreateAPIView):
    """
    Teacher can evaluate the task submissions.
    """
    queryset = TaskEvaluation.objects.all()
    serializer_class = TaskEvaluationSerialzer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrNotAllowed]

    def get_object(self):
        return super().get_object()

    def get_serializer_context(self):
        task_submission_id = self.kwargs["submission_id"]
        task_submission_obj = generics.get_object_or_404(
            TaskSubmission,
            id=task_submission_id
        )
        context = super().get_serializer_context()
        context["task_submission"] = task_submission_obj
        return context
    
class TaskEvaluationDetailAPIView(generics.RetrieveAPIView):
    """
    View the grade and feedback.
    """
    serializer_class = TaskEvaluationSerialzer
    permission_classes = [permissions.IsAuthenticated, CanViewTaskEvaluation]
    lookup_field = "submission_id"
    lookup_url_kwarg = "submission_id"

    def get_queryset(self):
        return TaskEvaluation.objects.all()
    

    
