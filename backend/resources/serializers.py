from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone
from classrooms.models import Classroom
from tasks.models import Task
from .models import Resource
from .utils import (
    detect_mime_type,
    get_allowed_mime_types,
    get_max_upload_size_bytes,
    scan_for_malware,
)
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
            "scan_status",
            "scan_message",
            "scanned_at",
            "target_type",
            "target_id",
        ]
        read_only_fields = [
            "id",
            "uploaded_by",
            "uploaded_at",
            "scan_status",
            "scan_message",
            "scanned_at",
        ]
        extra_kwargs = {
            "name": {"required": False, "allow_blank": True},
        }

    def get_target_type(self, obj):
        return obj.content_type.model

    def get_target_id(self, obj):
        return obj.object_id

    def validate_file(self, value):
        max_size_bytes = get_max_upload_size_bytes()
        if value.size > max_size_bytes:
            max_mb = max_size_bytes / (1024 * 1024)
            raise serializers.ValidationError(
                f"File size exceeds limit ({max_mb:.1f} MB)."
            )

        extension = os.path.splitext(value.name)[1].lower().lstrip(".")
        allowed_mimes = get_allowed_mime_types().get(extension, [])
        detected_mime = detect_mime_type(value)

        if not allowed_mimes or detected_mime not in allowed_mimes:
            raise serializers.ValidationError(
                f"Invalid file content for .{extension} upload. Detected MIME: {detected_mime}."
            )

        scan_ok, scan_message = scan_for_malware(value)
        if not scan_ok:
            raise serializers.ValidationError("Malware detected. Upload blocked.")

        self.context["resource_scan_status"] = Resource.SCAN_STATUS_CLEAN
        self.context["resource_scan_message"] = scan_message
        self.context["resource_scanned_at"] = timezone.now()
        return value

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

    def create(self, validated_data):
        validated_data["scan_status"] = self.context.get(
            "resource_scan_status", Resource.SCAN_STATUS_FAILED
        )
        validated_data["scan_message"] = self.context.get(
            "resource_scan_message", "Scan not completed."
        )
        validated_data["scanned_at"] = self.context.get("resource_scanned_at")
        return super().create(validated_data)
