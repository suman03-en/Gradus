from rest_framework import serializers
from .models import Classroom
from accounts.models import User

class StudentForeignKey(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return User.objects.filter(is_student=True)
    
class ClassroomSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    students = StudentForeignKey(many=True)
    class Meta:
        model = Classroom
        fields = (
            "id",
            "name",
            "description",
            "created_by",
            "invite_code",
            "created_at",
            "students",
        )

class InviteCodeSerializer(serializers.Serializer):
    invite_code = serializers.CharField()

class AddStudentSerializer(serializers.Serializer):
    """Teacher add students to classrooms by roll_no of students"""
    roll_no = serializers.CharField(required=False)
    roll_nos = serializers.ListField(
        child=serializers.CharField(),
        max_length=50,
        required=False,
        allow_empty = True
    )
    roll_no_range = serializers.CharField(required=False)
