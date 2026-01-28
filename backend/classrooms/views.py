from django.shortcuts import get_object_or_404
from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions

from .models import Classroom
from .serializers import ClassroomSerializer, InviteCodeSerializer
from .permissions import IsTeacherOrReadOnly, HasJoinedOrIsCreator

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
        return super().get_queryset().filter(created_by = user)
    
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
    

class ClassroomDetailView(generics.RetrieveAPIView):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [permissions.IsAuthenticated, HasJoinedOrIsCreator]
    lookup_field = "id"



class ClassroomJoinView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, ]
    def post(self, request):
        serializer = InviteCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite_code = serializer.validated_data.get("invite_code")  

        classroom = get_object_or_404(
            Classroom,
            invite_code=invite_code,
            is_active=True
        )

        if classroom.students.filter(id=request.user.id).exists():
            return Response(
                {"detail": "You have already joined this classroom"},
                status=status.HTTP_200_OK
            )
        
        classroom.students.add(request.user)

        return Response(
            {"detail": "Successfully joined the classroom"},
            status=status.HTTP_200_OK
        )
