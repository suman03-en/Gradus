import csv
import io
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()
from accounts.models import StudentProfile
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework import serializers as drf_serializers
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Task, TaskRecord
from .serializers import TaskSerializer, TaskRecordSerializer, TaskEvaluationSerializer
from .constants import TaskStatus, TaskMode
from accounts.permissions import (
    IsTeacherOrReadOnly,
    IsStudentOrReadOnly,
    IsTeacherOrNotAllowed,
)
from .permissions import (
    IsTaskCreatorOrClassroomStudent,
    CanViewTaskRecord,
    IsTaskRecordOwner,
)
from classrooms.models import Classroom


class TaskListCreateAPIView(generics.ListCreateAPIView):
    """
    Ability to list and create for teachers.
    Ability to list only for students.
    """

    serializer_class = TaskSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsTeacherOrReadOnly,
    )

    def get_queryset(self):
        classroom = self.get_classroom()
        queryset = Task.objects.prefetch_related("resources").filter(
            classroom=classroom, status=TaskStatus.PUBLISHED
        )
        return queryset

    def get_classroom(self):
        classroom_id = self.kwargs["uuid"]
        classroom = get_object_or_404(Classroom, id=classroom_id, is_active=True)

        user = self.request.user
        if user.is_student:
            if not classroom.is_student_member(user):
                raise PermissionDenied("You are not enrolled in this classroom.")
        else:
            if not classroom.is_teacher(user):
                raise PermissionDenied(
                    "Only classroom teachers can manage or view tasks."
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
            return Task.objects.prefetch_related("resources").filter(
                classroom__students=user
            )
        return (
            Task.objects.prefetch_related("resources")
            .filter(
                Q(classroom__created_by=self.request.user)
                | Q(classroom__teachers=self.request.user)
            )
            .distinct()
        )


class TaskRecordListCreateAPIView(generics.ListCreateAPIView):
    """
    Students submit tasks (POST with file for online tasks).
    Teachers/Students list task records (GET).
    """

    serializer_class = TaskRecordSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = (
        permissions.IsAuthenticated,
        IsStudentOrReadOnly,
        CanViewTaskRecord,
    )
    lookup_field = "id"
    lookup_url_kwarg = "uuid"

    def get_task(self):
        task_id = self.kwargs["uuid"]
        task = generics.get_object_or_404(Task, id=task_id)

        user = self.request.user
        classroom = task.classroom
        if user.is_student:
            if not classroom.is_student_member(user):
                raise PermissionDenied("You are not enrolled in this classroom.")
        else:
            if not classroom.is_teacher(user):
                raise PermissionDenied("Only classroom teachers can access records.")
        return task

    def get_queryset(self):
        if self.request.user.is_student:
            return TaskRecord.objects.filter(
                task=self.get_task(), student=self.request.user
            )
        return TaskRecord.objects.filter(task=self.get_task())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        task = self.get_task()
        context["task"] = task
        context["user"] = self.request.user
        return context


class TaskRecordUpdateAPIView(generics.UpdateAPIView):
    """Students update their submission file (before deadline)."""

    queryset = TaskRecord.objects.select_related("task", "student")
    serializer_class = TaskRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskRecordOwner]
    lookup_field = "id"
    lookup_url_kwarg = "record_id"

    def get_queryset(self):
        return self.queryset.filter(student=self.request.user)

    def get_serializer_context(self):
        """Add task context for validation."""
        context = super().get_serializer_context()
        submission = self.get_object()
        context["task"] = submission.task
        context["user"] = self.request.user
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
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TaskRecordEvaluationAPIView(generics.UpdateAPIView):
    """
    Teacher evaluates an EXISTING task record.
    Uses PATCH to update marks_obtained and feedback.
    """

    queryset = TaskRecord.objects.select_related("task", "student")
    serializer_class = TaskEvaluationSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrNotAllowed]
    lookup_field = "id"
    lookup_url_kwarg = "record_id"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        record = self.get_object()
        context["task_record"] = record
        context["allow_update"] = True
        return context


class TaskStudentEvaluationAPIView(generics.GenericAPIView):
    """
    Teacher evaluates a student on a task (Creating or Updating the record).
    Useful for manual grading where no submission record exists yet (offline tasks).
    """

    serializer_class = TaskEvaluationSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrNotAllowed]

    def get_task(self):
        return get_object_or_404(Task, id=self.kwargs["task_id"])

    def get_student(self):
        profile = get_object_or_404(
            StudentProfile, roll_no__iexact=self.kwargs["roll_no"]
        )
        return profile.user

    def get_record(self):
        return TaskRecord.objects.filter(
            task=self.get_task(), student=self.get_student()
        ).first()

    def post(self, request, *args, **kwargs):
        task = self.get_task()
        student = self.get_student()
        record = self.get_record()
        is_new_record = record is None

        # Verify task is offline (direct evaluation only for offline tasks)
        if task.mode != TaskMode.OFFLINE:
            return Response(
                {
                    "error": "Direct student evaluation is only available for offline tasks."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify teacher permission for this task
        if not task.classroom.is_teacher(request.user):
            return Response(
                {"error": "You do not have permission to evaluate this task."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Ensure student is in the classroom
        if not task.classroom.students.filter(id=student.id).exists():
            return Response(
                {"error": "Student is not in this classroom."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not record:
            record = TaskRecord(task=task, student=student)

        serializer = self.get_serializer(
            record,
            data=request.data,
            partial=True,
            context={"task_record": record, "allow_update": True},
        )

        if serializer.is_valid():
            serializer.save(evaluated_at=timezone.now())
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if is_new_record else status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskRecordDetailAPIView(generics.RetrieveAPIView):
    """
    View a task record (submission + evaluation details).
    """

    serializer_class = TaskRecordSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewTaskRecord]
    lookup_field = "id"
    lookup_url_kwarg = "record_id"

    def get_queryset(self):
        return TaskRecord.objects.select_related("task", "student").all()


class BulkEvaluationUploadSerializer(drf_serializers.Serializer):
    """Minimal serializer for DRF browsable API form rendering."""

    file = drf_serializers.FileField(
        help_text="CSV file with columns: Roll No, Marks, Feedback"
    )


class BulkTaskEvaluationAPIView(generics.GenericAPIView):
    """
    Bulk evaluate offline tasks using CSV upload.
    Teachers can upload a CSV with columns: student name, roll no, marks, feedback.
    """

    serializer_class = BulkEvaluationUploadSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrNotAllowed]
    queryset = Task.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "task_id"
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        task = self.get_object()

        if task.mode != TaskMode.OFFLINE:
            return Response(
                {"error": "Bulk upload is only for offline tasks."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify permissions: only task creator or classroom creator can evaluate
        if not task.classroom.is_teacher(request.user):
            return Response(
                {"error": "You do not have permission to evaluate this task."},
                status=status.HTTP_403_FORBIDDEN,
            )

        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            decoded_file = file.read().decode("utf-8")
            csv_data = list(csv.DictReader(io.StringIO(decoded_file)))
        except Exception as e:
            return Response(
                {"error": f"Error reading CSV file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not csv_data:
            return Response(
                {"error": "CSV is empty or invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        header = [h.strip().lower() for h in csv_data[0].keys()]
        if "roll no" not in header or "marks" not in header:
            return Response(
                {"error": "CSV must contain 'roll no' and 'marks' columns."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        classroom_students = task.classroom.students.all()

        success_count = 0
        errors = []

        with transaction.atomic():
            for index, row in enumerate(csv_data, start=2):
                row_normalized = {k.strip().lower(): v for k, v in row.items() if k}
                roll_no = row_normalized.get("roll no", "").strip()
                marks_str = row_normalized.get("marks", "").strip()
                feedback = row_normalized.get("feedback", "").strip()

                if not roll_no:
                    continue

                try:
                    marks = float(marks_str)
                    if marks < 0 or marks > task.full_marks:
                        errors.append(
                            f"Row {index}: Marks must be between 0 and {task.full_marks}."
                        )
                        continue
                except ValueError:
                    errors.append(f"Row {index}: Invalid marks format.")
                    continue

                student = classroom_students.filter(
                    student_profile__roll_no__iexact=roll_no
                ).first()
                if not student:
                    errors.append(
                        f"Row {index}: Student with roll no '{roll_no}' not found in classroom."
                    )
                    continue

                # Create or update the TaskRecord directly with marks
                TaskRecord.objects.update_or_create(
                    task=task,
                    student=student,
                    defaults={
                        "marks_obtained": marks,
                        "feedback": feedback,
                        "evaluated_at": timezone.now(),
                    },
                )
                success_count += 1

        status_code = status.HTTP_207_MULTI_STATUS if errors else status.HTTP_200_OK
        return Response(
            {"success": success_count, "errors": errors}, status=status_code
        )
