from rest_framework import serializers
from .models import Task

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
    
    
