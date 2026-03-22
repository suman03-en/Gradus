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
    resources = serializers.SerializerMethodField(read_only=True)
    
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
                "file_url": r.file.url if r.file and hasattr(r.file, 'url') else None,
                "uploaded_at": r.uploaded_at
            }
            for r in qs
        ]

class InviteCodeSerializer(serializers.Serializer):
    invite_code = serializers.CharField()

class AddStudentSerializer(serializers.Serializer):
    """Teacher add students to classrooms by roll_no of students"""
    roll_no = serializers.CharField(
        required=False,
        validators = [validate_roll_number])

