import uuid
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from .utils import generate_classroom_code
from tasks.constants import TaskType, TaskComponent


class Classroom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_classrooms",
    )
    invite_code = models.CharField(max_length=10, unique=True, editable=False)
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="joined_classrooms", blank=True
    )
    is_active = models.BooleanField(
        default=True
    )  # set is_active to False when deleting
    created_at = models.DateTimeField(auto_now_add=True)
    resources = GenericRelation("resources.Resource")

    def _check_unique(self, invite_code):
        qs = Classroom.objects.filter(invite_code=invite_code)
        if qs.exists():
            return False
        return True

    def save(self, *args, **kwargs):
        if not self.invite_code:
            new_code = generate_classroom_code()
            while not self._check_unique(new_code):
                new_code = generate_classroom_code()
            self.invite_code = new_code
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ClassroomTaskTypeWeightage(models.Model):
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="task_type_weightages",
    )
    task_type = models.CharField(
        max_length=20,
        choices=TaskType.choices,
        db_index=True,
    )
    assessment_component = models.CharField(
        max_length=10,
        choices=TaskComponent.choices,
        default=TaskComponent.THEORY,
        db_index=True,
    )
    include_in_final = models.BooleanField(default=False)
    weightage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["classroom", "assessment_component", "task_type"],
                name="unique_classroom_component_task_type_weightage",
            ),
            models.CheckConstraint(
                condition=Q(weightage__gte=0) & Q(weightage__lte=100),
                name="classroom_weightage_between_0_and_100",
            ),
            models.CheckConstraint(
                condition=(~Q(include_in_final=True) | Q(weightage__gt=0)),
                name="classroom_weightage_positive_when_included",
            ),
        ]
        ordering = ("assessment_component", "task_type")

    def __str__(self):
        return (
            f"{self.classroom.name} - {self.assessment_component} - "
            f"{self.task_type} ({self.weightage}%)"
        )
