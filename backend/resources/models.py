import uuid
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import FileExtensionValidator
from .utils import resource_upload_path


class Resource(models.Model):
    SCAN_STATUS_PENDING = "pending"
    SCAN_STATUS_CLEAN = "clean"
    SCAN_STATUS_INFECTED = "infected"
    SCAN_STATUS_FAILED = "failed"

    SCAN_STATUS_CHOICES = [
        (SCAN_STATUS_PENDING, "Pending"),
        (SCAN_STATUS_CLEAN, "Clean"),
        (SCAN_STATUS_INFECTED, "Infected"),
        (SCAN_STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    file = models.FileField(
        upload_to=resource_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "pdf",
                    "doc",
                    "docx",
                    "jpg",
                    "jpeg",
                    "png",
                    "txt",
                    "zip",
                    "pptx",
                ]
            )
        ],
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_resources",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    scan_status = models.CharField(
        max_length=16,
        choices=SCAN_STATUS_CHOICES,
        default=SCAN_STATUS_PENDING,
        db_index=True,
    )
    scan_message = models.CharField(max_length=255, blank=True, default="")
    scanned_at = models.DateTimeField(null=True, blank=True)

    # Generic Foreign Key fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["content_type", "object_id", "scan_status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.content_type})"
