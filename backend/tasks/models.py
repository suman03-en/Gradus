import uuid
from django.db import models
from django.conf import settings
from classrooms.models import Classroom
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import FileExtensionValidator
from .constants import (
    TaskStatus,
    TaskMode,
    TaskType
)
from .utils import submission_upload_path


class Task(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    end_date = models.DateTimeField()
    description = models.TextField(default="")
    full_marks = models.PositiveIntegerField(blank=False, null=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tasks"
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    status = models.CharField(
        max_length=10,
        choices=TaskStatus.choices,
        default=TaskStatus.DRAFT
    )
    mode = models.CharField(
        max_length=10,
        choices=TaskMode.choices,
        default=TaskMode.ONLINE
    )
    task_type = models.CharField(
        max_length=20,
        choices=TaskType.choices,
        default=TaskType.ASSIGNMENT
    )
    resources = GenericRelation("resources.Resource")

    def __str__(self):
        return self.name
    

class TaskRecord(models.Model):
    """
    Unified model representing a student's record for a task.
    For online tasks: stores the uploaded file AND marks/feedback after evaluation.
    For offline tasks: stores only marks/feedback (no file).
    """
    id = models.UUIDField(
    primary_key=True,
    default=uuid.uuid4,
    editable=False
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_file = models.FileField(
        upload_to=submission_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt', 'zip', 'pptx'])],
        null=True,
        blank=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Evaluation fields (merged from TaskEvaluation)
    marks_obtained = models.FloatField(null=True, blank=True)
    feedback = models.TextField(default="", blank=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("task", "student")
        db_table = "tasks_taskrecord"

    def __str__(self):
        return f"{self.student} - {self.task}"

    @property
    def is_evaluated(self):
        return self.marks_obtained is not None