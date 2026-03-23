from django.utils import timezone
from rest_framework import serializers
from tasks.constants import TaskMode
from .models import Task, TaskRecord


class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    resources = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id", "name", "created_at", "updated_at", "end_date", 
            "description", "full_marks", "created_by", "classroom", 
            "status", "mode", "task_type", "assessment_component", "resources"
        )
        read_only_fields = (
            "id",

            "created_at",
            "updated_at",
            "created_by",
            "classroom",
        )

    def create(self, validated_data):
        extra_data = {
            "created_by": self.context["user"],
            "classroom": self.context["classroom"],
        }
        validated_data.update(extra_data)
        return super().create(validated_data)

    def get_resources(self, obj):
        from django.contrib.contenttypes.models import ContentType
        from resources.models import Resource
        ct = ContentType.objects.get_for_model(Task)
        qs = Resource.objects.filter(content_type=ct, object_id=obj.id)
        return [
            {
                "id": str(r.id),
                "name": r.name,
                "file_url": r.file.url if r.file and hasattr(r.file, 'url') else None,
                "uploaded_at": r.uploaded_at
            }
            for r in qs
        ]



class TaskRecordSerializer(serializers.ModelSerializer):
    """Serializer for student submissions (online tasks)."""
    student_username = serializers.CharField(source="student.username", read_only=True)
    is_evaluated = serializers.BooleanField(read_only=True)

    class Meta:
        model = TaskRecord
        fields = (
            "id", "task", "student", "student_username",
            "uploaded_file", "submitted_at",
            "marks_obtained", "feedback", "evaluated_at", "is_evaluated"
        )
        read_only_fields = (
            "id", "task", "student", "submitted_at",
            "marks_obtained", "feedback", "evaluated_at"
        )

    def validate(self, attrs):
        """
        Object-level validation for business logic.
        
        Validates:
        - Task exists in context
        - Task deadline hasn't passed
        - Task is in ONLINE mode
        - Student hasn't already submitted
        """

        task = self.context.get("task")
        student = self.context.get("user")
        if not task:
            raise serializers.ValidationError({
                "task": "Task context is required."
            })
        if timezone.now() > task.end_date:
            raise serializers.ValidationError(
                {"submitted_at": "Submission deadline has passed."}
            )
        if task.mode != TaskMode.ONLINE:
            raise serializers.ValidationError(
                {"task": "This task does not accept online submissions."}
            )

        # For online tasks, ensure a file is provided
        has_file_in_instance = self.instance and self.instance.uploaded_file
        has_file_in_attrs = attrs.get('uploaded_file') is not None
        
        if not has_file_in_instance and not has_file_in_attrs:
            raise serializers.ValidationError(
                {"uploaded_file": "An uploaded file is required for online tasks."}
            )

        if not self.instance:
            if self.Meta.model.objects.filter(task=task, student=student).exists():
                raise serializers.ValidationError(
                    {
                       "detail": "You have already submitted this task."
                    }
                )
        
        attrs["task"] = task
        attrs["student"] = student
        return attrs
    
    def update(self, instance, validated_data):
        """
        Update submission - only allowed before deadline.
        
        Note: Deadline check happens in validate() method.
        """
        return super().update(instance, validated_data)


class TaskEvaluationSerializer(serializers.ModelSerializer):
    """Serializer for teacher evaluation (marks/feedback on a TaskRecord)."""
    class Meta:
        model = TaskRecord
        fields = ["marks_obtained", "feedback", "evaluated_at"]
        read_only_fields = ["evaluated_at"]

    def validate_marks_obtained(self, value):
        task_record = self.context["task_record"]
        task_fm = task_record.task.full_marks
        if value < 0 or value > task_fm:
            raise serializers.ValidationError(
                f"Marks must be between 0 and {task_fm}."
            )
        return value

    def validate_feedback(self, value):
        if not value.strip():
            raise serializers.ValidationError("Feedback cannot be empty.")
        return value

    def validate(self, attrs):
        task_record = self.context["task_record"]
        if task_record.is_evaluated and not self.context.get("allow_update", False):
            raise serializers.ValidationError(
                {"detail": "This record has already been evaluated."}
            )
        return super().validate(attrs)

    def update(self, instance, validated_data):
        validated_data["evaluated_at"] = timezone.now()
        return super().update(instance, validated_data)
