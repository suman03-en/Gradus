from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from classrooms.models import Classroom
from tasks.models import Task
from .models import Resource
import os


class ResourceSerializer(serializers.ModelSerializer):
    content_type = serializers.ChoiceField(
        choices=[("classroom", "Classroom"), ("task", "Task")], write_only=True
    )
    object_id = serializers.UUIDField(write_only=True)

    # Read-only attributes to expose the resolved content type if needed
    target_type = serializers.SerializerMethodField(read_only=True)
    target_id = serializers.SerializerMethodField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")

        # Populate object_id as a dropdown dynamically for the logged-in user
        if request and hasattr(request, "user") and request.user.is_authenticated:
            user = request.user
            choices = []

            # Fetch all classrooms/tasks where this teacher has management access.
            for c in Classroom.objects.filter(
                Q(created_by=user) | Q(teachers=user)
            ).distinct():
                choices.append((str(c.id), f"Classroom: {c.name}"))

            for t in Task.objects.filter(
                Q(created_by=user)
                | Q(classroom__created_by=user)
                | Q(classroom__teachers=user)
            ).distinct():
                choices.append((str(t.id), f"Task: {t.name}"))

            if choices:
                self.fields["object_id"] = serializers.ChoiceField(
                    choices=choices, write_only=True
                )

    class Meta:
        model = Resource
        fields = [
            "id",
            "name",
            "file",
            "content_type",
            "object_id",
            "uploaded_by",
            "uploaded_at",
            "target_type",
            "target_id",
        ]
        read_only_fields = ["id", "uploaded_by", "uploaded_at"]

    def get_target_type(self, obj):
        return obj.content_type.model

    def get_target_id(self, obj):
        return obj.object_id

    def validate(self, attrs):
        # We only need to validate content_type and object_id during creation
        if not self.instance:
            ct_model = attrs.get("content_type")
            object_id = attrs.get("object_id")

            if ct_model not in ["classroom", "task"]:
                raise serializers.ValidationError(
                    {"content_type": "Must be 'classroom' or 'task'."}
                )

            try:
                ct = ContentType.objects.get(model=ct_model)
                obj = ct.get_object_for_this_type(id=object_id)
            except ContentType.DoesNotExist:
                raise serializers.ValidationError(
                    {"content_type": "Invalid content type."}
                )
            except Exception:
                raise serializers.ValidationError({"object_id": "Object not found."})

            # Replace the string with the actual ContentType instance
            attrs["content_type"] = ct

            # Auto-fill name if not provided
            if "name" not in attrs or not attrs["name"]:
                file_obj = attrs.get("file")
                if file_obj:
                    attrs["name"] = os.path.basename(file_obj.name)

        return attrs
