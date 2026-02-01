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
    def create(self, validated_data):
        validated_data["task"] = self.context["task"]
        validated_data["student"] = self.context["user"]
        return super().create(validated_data)
