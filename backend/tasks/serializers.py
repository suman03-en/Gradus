from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        Model = Task
        fields = "__all__"
        read_only_fields = (
            "id", 
            "created_at",
            "updated_at",
            "created_by",
            "classroom",
            )
