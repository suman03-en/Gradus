import uuid
from django.db import models
from django.conf import settings
from classrooms.models import Classroom
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
    full_marks = models.PositiveIntegerField()
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

    def __str__(self):
        return self.name
    

class TaskSubmission(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_file = models.FileField(upload_to=submission_upload_path)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("task", "student")


class TaskEvaluation(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    submission = models.OneToOneField(TaskSubmission, on_delete=models.CASCADE)
    marks_obtained = models.FloatField()


    