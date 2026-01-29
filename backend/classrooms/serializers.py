from rest_framework import serializers
from .models import Classroom
from accounts.models import User
from accounts.validators import validate_roll_number

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
    roll_no = serializers.CharField(
        required=False,
        validators = [validate_roll_number])

