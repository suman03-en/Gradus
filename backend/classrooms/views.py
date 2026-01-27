from rest_framework import generics
from rest_framework import permissions

from .models import Classroom
from .serializers import ClassroomSerializer
from .permissions import IsTeacherOrReadOnly

class ClassroomListCreateView(generics.ListCreateAPIView):
    """
    Accepts: GET, POST
    Returns:
    Teacher:
        GET: List all the created classrooms
        POST: Create the new classrooms
    Student:
        GET: List  all the joined classrooms
    """
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsTeacherOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_student:
            return user.joined_classrooms
        return self.queryset.filter(created_by = user)
    
    def get_serializer_context(self):
        """
        Override this method to send the extra context to the serializer
        """
        user = self.request.user
        context = super().get_serializer_context()
        context["user"] = user
        return context
    
    def perform_create(self, serializer):
        return serializer.save(created_by=self.request.user)
    
    