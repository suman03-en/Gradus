from rest_framework import serializers
from .models import (
    Classroom,
    ClassroomTaskTypeWeightage,
    ClassroomAttendanceWeightage,
)
from accounts.models import User
from accounts.validators import validate_roll_number
from tasks.constants import TaskType, TaskComponent


class StudentForeignKey(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return User.objects.filter(is_student=True)


class ClassroomSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    students = StudentForeignKey(many=True)
    teachers = serializers.SerializerMethodField(read_only=True)
    resources = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Classroom
        fields = (
            "id",
            "name",
            "description",
            "created_by",
            "teachers",
            "invite_code",
            "created_at",
            "students",
            "resources",
        )

    def get_resources(self, obj):
        from django.contrib.contenttypes.models import ContentType
        from resources.models import Resource

        ct = ContentType.objects.get_for_model(Classroom)
        qs = Resource.objects.filter(content_type=ct, object_id=obj.id)
        # return basic payload so frontend doesn't need a second fetch
        return [
            {
                "id": str(r.id),
                "name": r.name,
                "file_url": r.file.url if r.file and hasattr(r.file, "url") else None,
                "uploaded_at": r.uploaded_at,
            }
            for r in qs
        ]

    def get_teachers(self, obj):
        teacher_usernames = [obj.created_by.username]
        teacher_usernames.extend(obj.teachers.values_list("username", flat=True))
        # Preserve order while removing duplicates.
        return list(dict.fromkeys(teacher_usernames))


class InviteCodeSerializer(serializers.Serializer):
    invite_code = serializers.CharField()


class AddStudentSerializer(serializers.Serializer):
    """Teacher add students to classrooms by roll_no of students"""

    roll_no = serializers.CharField(required=True, validators=[validate_roll_number])


class AddTeacherSerializer(serializers.Serializer):
    """Classroom owner can add co-teachers by username."""

    username = serializers.CharField(required=True)


class ClassroomTaskTypeWeightageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomTaskTypeWeightage
        fields = (
            "assessment_component",
            "task_type",
            "include_in_final",
            "weightage",
        )

    def validate(self, attrs):
        include_in_final = attrs.get("include_in_final", False)
        weightage = attrs.get("weightage", 0)

        if include_in_final and weightage <= 0:
            raise serializers.ValidationError(
                {
                    "weightage": "Weightage must be greater than 0 for included task types."
                }
            )
        if not include_in_final:
            attrs["weightage"] = 0

        return attrs


class ClassroomAttendanceWeightageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomAttendanceWeightage
        fields = (
            "assessment_component",
            "include_in_final",
            "weightage",
        )

    def validate(self, attrs):
        include_in_final = attrs.get("include_in_final", False)
        weightage = attrs.get("weightage", 0)

        if include_in_final and weightage <= 0:
            raise serializers.ValidationError(
                {
                    "weightage": "Weightage must be greater than 0 for included attendance."
                }
            )
        if not include_in_final:
            attrs["weightage"] = 0
        return attrs


class AttendanceEntrySerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    is_present = serializers.BooleanField()


class AttendanceSessionUpsertSerializer(serializers.Serializer):
    date = serializers.DateField()
    assessment_component = serializers.ChoiceField(choices=TaskComponent.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)
    entries = AttendanceEntrySerializer(many=True)

    def validate_entries(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one attendance entry is required."
            )

        seen = set()
        for item in value:
            sid = str(item["student_id"])
            if sid in seen:
                raise serializers.ValidationError(
                    "Duplicate student_id in attendance entries."
                )
            seen.add(sid)
        return value


class ClassroomWeightageConfigSerializer(serializers.Serializer):
    weightages = ClassroomTaskTypeWeightageSerializer(many=True)
    attendance_weightages = ClassroomAttendanceWeightageSerializer(
        many=True, required=False
    )

    def validate_weightages(self, value):
        seen_pairs = set()
        allowed_task_types = {choice for choice, _ in TaskType.choices}
        allowed_components = {choice for choice, _ in TaskComponent.choices}
        totals_by_component = {
            TaskComponent.THEORY: 0,
            TaskComponent.LAB: 0,
        }

        for item in value:
            task_type = item["task_type"]
            assessment_component = item["assessment_component"]

            if task_type not in allowed_task_types:
                raise serializers.ValidationError(
                    f"'{task_type}' is not a valid task type."
                )

            if assessment_component not in allowed_components:
                raise serializers.ValidationError(
                    f"'{assessment_component}' is not a valid assessment component."
                )

            pair = (assessment_component, task_type)
            if pair in seen_pairs:
                raise serializers.ValidationError(
                    "Duplicate component-task_type pair "
                    f"'{assessment_component}:{task_type}' is not allowed."
                )
            seen_pairs.add(pair)

            if item.get("include_in_final"):
                totals_by_component[assessment_component] += item["weightage"]

        for component, total in totals_by_component.items():
            if total > 100:
                raise serializers.ValidationError(
                    f"Total included weightage for '{component}' cannot exceed 100."
                )

        return value

    def validate(self, attrs):
        task_weightages = attrs.get("weightages", [])
        attendance_weightages = attrs.get("attendance_weightages", [])

        allowed_components = {choice for choice, _ in TaskComponent.choices}
        attendance_seen = set()
        attendance_totals = {
            TaskComponent.THEORY: 0,
            TaskComponent.LAB: 0,
        }
        task_totals = {
            TaskComponent.THEORY: 0,
            TaskComponent.LAB: 0,
        }

        for item in task_weightages:
            if item.get("include_in_final"):
                task_totals[item["assessment_component"]] += item["weightage"]

        for item in attendance_weightages:
            comp = item["assessment_component"]
            if comp not in allowed_components:
                raise serializers.ValidationError(
                    {"attendance_weightages": f"'{comp}' is not a valid component."}
                )

            if comp in attendance_seen:
                raise serializers.ValidationError(
                    {
                        "attendance_weightages": "Duplicate attendance weightage component is not allowed."
                    }
                )
            attendance_seen.add(comp)

            if item.get("include_in_final"):
                attendance_totals[comp] += item["weightage"]

        for comp in [TaskComponent.THEORY, TaskComponent.LAB]:
            total_for_component = task_totals[comp] + attendance_totals[comp]
            if total_for_component > 100:
                raise serializers.ValidationError(
                    {
                        "attendance_weightages": (
                            f"Total included weightage for '{comp}' including attendance "
                            f"cannot exceed 100. Current total: {total_for_component}."
                        )
                    }
                )

        return attrs
