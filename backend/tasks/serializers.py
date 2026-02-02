from rest_framework import serializers
from .models import Task, TaskSubmission

class TaskSerializer(serializers.ModelSerializer):
    
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
            "classroom": self.context["classroom"]
        }
        validated_data.update(extra_data)
        return super().create(validated_data)
    

class TaskSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model= TaskSubmission
        fields = (
            "id",
            "task",
            "student", 
            "uploaded_file", "submitted_at"
        )
        read_only_fields = (
            "id",
            "task",
            "student",
            "submitted_at"
        )

    def validate(self, attrs):
        task = self.context["task"]
        student = self.context["user"]
        if self.Meta.model.objects.filter(task=task, student=student).exists():
            raise serializers.ValidationError({
            "submission_error": "You can't submit more than once for the same task."
        })
        attrs["task"] = task
        attrs["student"] = student
        return attrs
    
