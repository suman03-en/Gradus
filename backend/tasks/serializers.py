from django.utils import timezone
from rest_framework import serializers
from tasks.constants import TaskMode
from .models import Task, TaskSubmission, TaskEvaluation


class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Task
        fields = "__all__"
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


class TaskSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSubmission
        fields = ("id", "task", "student", "uploaded_file", "submitted_at")
        read_only_fields = ("id", "task", "student", "submitted_at")

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


class TaskEvaluationSerialzer(serializers.ModelSerializer):
    class Meta:
        model = TaskEvaluation
        fields = ["marks_obtained", "feedback"]
        read_only_fields = ["submission"]

    def validate_marks_obtained(self, value):
        task_fm = self.context["task_submission"].task.full_marks
        if value < 0 or value > task_fm:
            raise serializers.ValidationError(
                {
                    "details": "You cannot assign the marks less than zero or greater than full marks."
                }
            )
        return value

    def validate_feedback(self, value):
        if not value.strip():
            raise serializers.ValidationError({"details": "Feedback cannot be empty."})
        return value

    def validate(self, attrs):
        submission = self.context["task_submission"]
        if TaskEvaluation.objects.filter(submission=submission).exists():
            raise serializers.ValidationError(
                {"details": "This submission has already been evaluated."}
            )
        attrs["submission"] = submission
        return super().validate(attrs)
