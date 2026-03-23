from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions

from .models import Classroom, ClassroomTaskTypeWeightage
from .serializers import (
    ClassroomSerializer,
    InviteCodeSerializer,
    AddStudentSerializer,
    ClassroomTaskTypeWeightageSerializer,
    ClassroomWeightageConfigSerializer,
)
from .permissions import HasJoinedOrIsCreator
from accounts.permissions import IsTeacherOrNotAllowed, IsTeacherOrReadOnly, IsCreator
from accounts.models import StudentProfile
from tasks.constants import TaskComponent
from .utils import (
    is_valid_component_filter,
    build_classroom_gradebook_payload,
    build_weightage_config_payload,
    upsert_classroom_weightages,
    build_gradebook_excel_file,
)


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

    queryset = Classroom.objects.prefetch_related("resources").all()
    serializer_class = ClassroomSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsTeacherOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_student:
            return user.joined_classrooms.prefetch_related("resources").all()
        return super().get_queryset().filter(created_by=user)

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
    lookup_url_kwarg = "uuid"


class ClassroomJoinView(generics.GenericAPIView):
    serializer_class = InviteCodeSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite_code = serializer.validated_data.get("invite_code")

        classroom = get_object_or_404(
            Classroom, invite_code=invite_code, is_active=True
        )

        if classroom.students.filter(id=request.user.id).exists():
            return Response(
                {"detail": "You have already joined this classroom"},
                status=status.HTTP_200_OK,
            )

        classroom.students.add(request.user)

        return Response(
            {"detail": "Successfully joined the classroom"}, status=status.HTTP_200_OK
        )


class ClassroomAddStudentView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated, IsTeacherOrNotAllowed)
    serializer_class = AddStudentSerializer

    def get_classroom(self, classroom_id):
        return get_object_or_404(Classroom, id=classroom_id, is_active=True)

    def post(self, request, **kwargs):
        classroom = self.get_classroom(kwargs["uuid"])
        # Enforce that only the classroom creator can add students
        if classroom.created_by != request.user:
            return Response(
                {"detail": "Only the classroom creator can add students."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roll_no = serializer.validated_data["roll_no"]
        student_profile = get_object_or_404(StudentProfile, roll_no=roll_no)
        student = student_profile.user
        if classroom.students.filter(id=student.id).exists():
            return Response(
                {
                    "detail": "Student with this roll_no has already joined this classroom"
                },
                status=status.HTTP_200_OK,
            )
        classroom.students.add(student)

        return Response(
            {"detail": "Successfully added to the classroom"}, status=status.HTTP_200_OK
        )


class ClassroomGradebookAPIView(generics.RetrieveAPIView):
    """
    Returns an optimized gradebook payload for a classroom.
    For teachers, it returns the performance of all students in the classroom.
    For students, it returns only their own performance.
    """

    queryset = Classroom.objects.all()
    permission_classes = [permissions.IsAuthenticated, HasJoinedOrIsCreator]
    lookup_field = "id"
    lookup_url_kwarg = "uuid"

    def retrieve(self, request, *args, **kwargs):
        classroom = self.get_object()

        component_filter = request.query_params.get("component")
        if not is_valid_component_filter(component_filter):
            return Response(
                {
                    "detail": "Invalid component filter. Use 'theory' or 'lab'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = build_classroom_gradebook_payload(
            classroom=classroom,
            user=request.user,
            component_filter=component_filter,
        )

        return Response(data, status=status.HTTP_200_OK)


class ClassroomGradebookExcelExportAPIView(generics.RetrieveAPIView):
    queryset = Classroom.objects.all()
    permission_classes = [permissions.IsAuthenticated, HasJoinedOrIsCreator]
    lookup_field = "id"
    lookup_url_kwarg = "uuid"

    def retrieve(self, request, *args, **kwargs):
        component = request.query_params.get("component")
        if not component:
            return Response(
                {"detail": "component query param is required (theory or lab)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not is_valid_component_filter(component):
            return Response(
                {"detail": "Invalid component filter. Use 'theory' or 'lab'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        classroom = self.get_object()

        try:
            file_bytes, filename = build_gradebook_excel_file(
                classroom=classroom,
                user=request.user,
                component=component,
            )
        except ImportError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = HttpResponse(
            file_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ClassroomWeightageConfigAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), HasJoinedOrIsCreator()]
        return [permissions.IsAuthenticated(), IsTeacherOrNotAllowed()]

    def get_classroom(self):
        return get_object_or_404(Classroom, id=self.kwargs["uuid"], is_active=True)

    def get(self, request, *args, **kwargs):
        classroom = self.get_classroom()

        weightage_summary = build_weightage_config_payload(classroom)

        return Response(
            {
                "classroom": {"id": str(classroom.id), "name": classroom.name},
                **weightage_summary,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, *args, **kwargs):
        classroom = self.get_classroom()

        if classroom.created_by != request.user:
            return Response(
                {
                    "detail": "Only the classroom creator can update weightage configuration."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ClassroomWeightageConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upsert_classroom_weightages(
            classroom=classroom,
            weightages_data=serializer.validated_data["weightages"],
        )

        output = ClassroomTaskTypeWeightage.objects.filter(classroom=classroom)
        response_data = ClassroomTaskTypeWeightageSerializer(output, many=True).data
        weightage_summary = build_weightage_config_payload(classroom)

        return Response(
            {
                "classroom": {"id": str(classroom.id), "name": classroom.name},
                "weightages": response_data,
                "total_configured_weightage": weightage_summary[
                    "total_configured_weightage"
                ],
                "total_configured_weightage_by_component": weightage_summary[
                    "total_configured_weightage_by_component"
                ],
            },
            status=status.HTTP_200_OK,
        )
