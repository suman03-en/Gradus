from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db import models
from django.db import transaction
import csv
import io
from django.contrib.auth import get_user_model
from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from .models import (
    Classroom,
    ClassroomTaskTypeWeightage,
    AttendanceSession,
    AttendanceRecord,
    AttendanceSummary,
    ClassroomAttendanceWeightage,
)
from .serializers import (
    ClassroomSerializer,
    InviteCodeSerializer,
    AddStudentSerializer,
    AddTeacherSerializer,
    ClassroomTaskTypeWeightageSerializer,
    ClassroomAttendanceWeightageSerializer,
    ClassroomWeightageConfigSerializer,
    AttendanceSessionUpsertSerializer,
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
    upsert_classroom_attendance_weightages,
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

    queryset = Classroom.objects.prefetch_related(
        "resources", "created_by", "teachers", "students"
    ).all()
    serializer_class = ClassroomSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsTeacherOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_student:
            return user.joined_classrooms.prefetch_related(
                "resources", "created_by", "teachers"
            ).all()
        return (
            super()
            .get_queryset()
            .filter(models.Q(created_by=user) | models.Q(teachers=user))
            .distinct()
        )

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


class ClassroomDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Classroom.objects.prefetch_related(
        "resources", "created_by", "teachers", "students"
    ).all()
    serializer_class = ClassroomSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "uuid"

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated(), HasJoinedOrIsCreator()]
        return [permissions.IsAuthenticated(), IsTeacherOrNotAllowed(), IsCreator()]


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
        # Allow owner and co-teachers to add students.
        if not classroom.is_teacher(request.user):
            return Response(
                {"detail": "Only classroom teachers can add students."},
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


class ClassroomAddTeacherView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated, IsTeacherOrNotAllowed)
    serializer_class = AddTeacherSerializer

    def get_classroom(self, classroom_id):
        return get_object_or_404(Classroom, id=classroom_id, is_active=True)

    def post(self, request, **kwargs):
        classroom = self.get_classroom(kwargs["uuid"])
        # Only classroom owner can manage co-teachers.
        if classroom.created_by != request.user:
            return Response(
                {"detail": "Only the classroom owner can add co-teachers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"].strip()

        teacher = get_object_or_404(
            get_user_model(),
            username__iexact=username,
            is_student=False,
        )

        if teacher == classroom.created_by:
            return Response(
                {"detail": "Classroom owner is already the lead teacher."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if classroom.teachers.filter(id=teacher.id).exists():
            return Response(
                {"detail": "This teacher is already added to the classroom."},
                status=status.HTTP_200_OK,
            )

        classroom.teachers.add(teacher)
        return Response(
            {"detail": f"Successfully added @{teacher.username} as co-teacher."},
            status=status.HTTP_200_OK,
        )


class ClassroomGradebookAPIView(generics.RetrieveAPIView):
    """
    Returns an optimized gradebook payload for a classroom.
    For teachers, it returns the performance of all students in the classroom.
    For students, it returns only their own performance.
    """

    queryset = (
        Classroom.objects.select_related("created_by")
        .prefetch_related("students", "teachers", "tasks")
        .all()
    )
    permission_classes = [permissions.IsAuthenticated, HasJoinedOrIsCreator]
    lookup_field = "id"
    lookup_url_kwarg = "uuid"

    def retrieve(self, request, *args, **kwargs):
        classroom = self.get_object()

        component_filter = request.query_params.get("component")
        if not is_valid_component_filter(component_filter):
            return Response(
                {"detail": "Invalid component filter. Use 'theory' or 'lab'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = build_classroom_gradebook_payload(
            classroom=classroom,
            user=request.user,
            component_filter=component_filter,
        )

        return Response(data, status=status.HTTP_200_OK)


class ClassroomGradebookExcelExportAPIView(generics.RetrieveAPIView):
    queryset = (
        Classroom.objects.select_related("created_by")
        .prefetch_related("students", "teachers", "tasks")
        .all()
    )
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
        classroom = get_object_or_404(Classroom, id=self.kwargs["uuid"], is_active=True)
        if self.request.user.is_student:
            has_access = classroom.is_student_member(self.request.user)
        else:
            has_access = classroom.is_teacher(self.request.user)
        if not has_access:
            raise PermissionDenied("You do not have access to this classroom.")
        return classroom

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

        if not classroom.is_teacher(request.user):
            return Response(
                {
                    "detail": "Only classroom teachers can update weightage configuration."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ClassroomWeightageConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upsert_classroom_weightages(
            classroom=classroom,
            weightages_data=serializer.validated_data["weightages"],
        )
        upsert_classroom_attendance_weightages(
            classroom=classroom,
            attendance_weightages_data=serializer.validated_data.get(
                "attendance_weightages", []
            ),
        )

        output = ClassroomTaskTypeWeightage.objects.filter(classroom=classroom)
        attendance_output = ClassroomAttendanceWeightage.objects.filter(
            classroom=classroom
        )
        response_data = ClassroomTaskTypeWeightageSerializer(output, many=True).data
        attendance_response_data = ClassroomAttendanceWeightageSerializer(
            attendance_output, many=True
        ).data
        weightage_summary = build_weightage_config_payload(classroom)

        return Response(
            {
                "classroom": {"id": str(classroom.id), "name": classroom.name},
                "weightages": response_data,
                "attendance_weightages": attendance_response_data,
                "total_configured_weightage": weightage_summary[
                    "total_configured_weightage"
                ],
                "total_configured_weightage_by_component": weightage_summary[
                    "total_configured_weightage_by_component"
                ],
            },
            status=status.HTTP_200_OK,
        )


class ClassroomAttendanceAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AttendanceSessionUpsertSerializer

    def get_classroom(self):
        classroom = get_object_or_404(Classroom, id=self.kwargs["uuid"], is_active=True)
        if self.request.user.is_student:
            has_access = classroom.is_student_member(self.request.user)
        else:
            has_access = classroom.is_teacher(self.request.user)
        if not has_access:
            raise PermissionDenied("You do not have access to this classroom.")
        return classroom

    def _ensure_teacher(self, classroom):
        if not classroom.is_teacher(self.request.user):
            raise PermissionDenied("Only classroom teachers can manage attendance.")

    def _upsert_one_session(self, classroom, payload):
        assessment_component = payload["assessment_component"]
        session_date = payload["date"]
        note = payload.get("note", "")
        entries = payload["entries"]

        classroom_student_ids = set(classroom.students.values_list("id", flat=True))
        incoming_student_ids = {entry["student_id"] for entry in entries}

        invalid_student_ids = incoming_student_ids - classroom_student_ids
        if invalid_student_ids:
            raise PermissionDenied(
                "Attendance includes students not enrolled in this classroom."
            )

        session, _ = AttendanceSession.objects.update_or_create(
            classroom=classroom,
            assessment_component=assessment_component,
            date=session_date,
            defaults={
                "note": note,
                "created_by": self.request.user,
            },
        )

        for entry in entries:
            AttendanceRecord.objects.update_or_create(
                session=session,
                student_id=entry["student_id"],
                defaults={"is_present": entry["is_present"]},
            )

        return session

    def get(self, request, *args, **kwargs):
        classroom = self.get_classroom()
        is_teacher = classroom.is_teacher(request.user)

        sessions_qs = AttendanceSession.objects.filter(classroom=classroom).order_by(
            "-date", "assessment_component"
        )
        records_qs = AttendanceRecord.objects.filter(
            session__classroom=classroom
        ).select_related("session", "student", "student__student_profile")

        if not is_teacher:
            records_qs = records_qs.filter(student=request.user)

        summary = {}
        summary_by_component = {}
        for rec in records_qs:
            key = str(rec.student_id)
            comp = rec.session.assessment_component
            if key not in summary:
                roll_no = None
                profile = getattr(rec.student, "student_profile", None)
                if profile:
                    roll_no = profile.roll_no
                summary[key] = {
                    "student_id": key,
                    "username": rec.student.username,
                    "roll_no": roll_no or rec.student.username,
                    "present": 0,
                    "total": 0,
                    "percentage": 0,
                }
            summary_by_component.setdefault(key, {})
            summary_by_component[key].setdefault(comp, {"present": 0, "total": 0})
            summary_by_component[key][comp]["total"] += 1
            if rec.is_present:
                summary_by_component[key][comp]["present"] += 1

        summary_qs = AttendanceSummary.objects.filter(classroom=classroom)
        if not is_teacher:
            summary_qs = summary_qs.filter(student=request.user)
        for row in summary_qs.select_related("student", "student__student_profile"):
            key = str(row.student_id)
            roll_no = (
                row.student.student_profile.roll_no
                if hasattr(row.student, "student_profile")
                and row.student.student_profile
                and row.student.student_profile.roll_no
                else row.student.username
            )
            existing = summary.get(
                key,
                {
                    "student_id": key,
                    "username": row.student.username,
                    "roll_no": roll_no,
                    "present": 0,
                    "total": 0,
                    "percentage": 0,
                },
            )
            summary[key] = existing
            summary_by_component.setdefault(key, {})
            summary_by_component[key][row.assessment_component] = {
                "present": row.present_days,
                "total": row.total_days,
            }

        for key, components in summary_by_component.items():
            present = sum(item["present"] for item in components.values())
            total = sum(item["total"] for item in components.values())
            summary[key]["present"] = present
            summary[key]["total"] = total
            summary[key]["percentage"] = (
                round((present / total) * 100, 2) if total > 0 else 0
            )

        session_records_map = {}
        for rec in records_qs:
            session_key = str(rec.session_id)
            if session_key not in session_records_map:
                session_records_map[session_key] = []
            session_records_map[session_key].append(
                {
                    "student_id": str(rec.student_id),
                    "username": rec.student.username,
                    "roll_no": (
                        rec.student.student_profile.roll_no
                        if hasattr(rec.student, "student_profile")
                        and rec.student.student_profile
                        and rec.student.student_profile.roll_no
                        else rec.student.username
                    ),
                    "is_present": rec.is_present,
                }
            )

        sessions_payload = []
        for session in sessions_qs:
            session_key = str(session.id)
            records = session_records_map.get(session_key, [])
            if not is_teacher and not records:
                continue
            sessions_payload.append(
                {
                    "id": session_key,
                    "date": session.date,
                    "assessment_component": session.assessment_component,
                    "note": session.note,
                    "records": records,
                }
            )

        response_summary = list(summary.values())
        if not is_teacher:
            response_summary = response_summary[:1]

        return Response(
            {
                "classroom": {"id": str(classroom.id), "name": classroom.name},
                "is_teacher": is_teacher,
                "attendance_summary": response_summary,
                "sessions": sessions_payload,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        classroom = self.get_classroom()
        self._ensure_teacher(classroom)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = self._upsert_one_session(classroom, serializer.validated_data)

        return Response(
            {
                "detail": "Attendance saved successfully.",
                "session_id": str(session.id),
            },
            status=status.HTTP_200_OK,
        )


class ClassroomAttendanceBulkCSVUploadAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_classroom(self):
        classroom = get_object_or_404(Classroom, id=self.kwargs["uuid"], is_active=True)
        if not classroom.is_teacher(self.request.user):
            raise PermissionDenied("Only classroom teachers can upload attendance CSV.")
        return classroom

    def post(self, request, *args, **kwargs):
        classroom = self.get_classroom()
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"detail": "CSV file is required in 'file' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            decoded = io.TextIOWrapper(file.file, encoding="utf-8")
            reader = csv.DictReader(decoded)
        except Exception:
            return Response(
                {"detail": "Unable to read CSV file. Ensure UTF-8 CSV format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        required_columns = {
            "assessment_component",
            "roll_no",
            "present_days",
            "total_days",
        }
        incoming_columns = set(reader.fieldnames or [])
        missing = sorted(required_columns - incoming_columns)
        if missing:
            return Response(
                {
                    "detail": (
                        "CSV missing required columns: " + ", ".join(missing) + ". "
                        "Required: assessment_component, roll_no, present_days, total_days. "
                        "Optional: note"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrolled_profiles = StudentProfile.objects.filter(
            user__in=classroom.students.all()
        ).select_related("user")
        student_by_roll = {
            (profile.roll_no or "").strip().upper(): profile.user_id
            for profile in enrolled_profiles
            if profile.roll_no
        }

        grouped = {}
        row_errors = []

        for idx, row in enumerate(reader, start=2):
            raw_component = (row.get("assessment_component") or "").strip().lower()
            raw_roll = (row.get("roll_no") or "").strip().upper()
            raw_present_days = (row.get("present_days") or "").strip()
            raw_total_days = (row.get("total_days") or "").strip()
            raw_note = (row.get("note") or "").strip()

            if not raw_component or not raw_roll:
                row_errors.append(
                    f"Row {idx}: assessment_component and roll_no are required."
                )
                continue

            if raw_component not in {TaskComponent.THEORY, TaskComponent.LAB}:
                row_errors.append(
                    f"Row {idx}: invalid assessment_component '{raw_component}'."
                )
                continue

            try:
                present_days = int(raw_present_days)
                total_days = int(raw_total_days)
            except ValueError:
                row_errors.append(
                    f"Row {idx}: present_days and total_days must be integers."
                )
                continue

            if present_days < 0 or total_days < 0:
                row_errors.append(
                    f"Row {idx}: present_days and total_days must be non-negative."
                )
                continue

            if present_days > total_days:
                row_errors.append(
                    f"Row {idx}: present_days cannot be greater than total_days."
                )
                continue

            student_id = student_by_roll.get(raw_roll)
            if not student_id:
                row_errors.append(
                    f"Row {idx}: roll_no '{raw_roll}' not found in this classroom."
                )
                continue

            key = (raw_roll, raw_component)
            grouped.setdefault(
                key,
                {
                    "student_id": student_id,
                    "assessment_component": raw_component,
                    "note": raw_note,
                    "present_days": 0,
                    "total_days": 0,
                },
            )
            if raw_note and not grouped[key]["note"]:
                grouped[key]["note"] = raw_note
            grouped[key]["present_days"] += present_days
            grouped[key]["total_days"] += total_days

        for key, payload in grouped.items():
            if payload["present_days"] > payload["total_days"]:
                row_errors.append(
                    f"Row group {key[0]}-{key[1]}: total present_days exceeds total_days."
                )

        if row_errors:
            return Response(
                {
                    "detail": "CSV validation failed.",
                    "errors": row_errors[:20],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not grouped:
            return Response(
                {"detail": "No valid attendance rows found in CSV."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        saved = []
        with transaction.atomic():
            for (_roll, _component), payload in grouped.items():
                summary, _ = AttendanceSummary.objects.update_or_create(
                    classroom=classroom,
                    student_id=payload["student_id"],
                    assessment_component=payload["assessment_component"],
                    defaults={
                        "present_days": payload["present_days"],
                        "total_days": payload["total_days"],
                        "updated_by": request.user,
                    },
                )
                saved.append(str(summary.id))

        return Response(
            {
                "detail": "Attendance summary CSV uploaded successfully.",
                "saved_summaries": saved,
            },
            status=status.HTTP_200_OK,
        )
