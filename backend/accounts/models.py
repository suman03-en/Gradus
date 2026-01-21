import uuid
from django.db import models
from django.conf import settings
from .validators import validate_roll_number
from .constants import Semester, Department, Section

class StudentProfile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="students_profile"
    )
    roll_no = models.CharField(
        max_length=150,
        unique=True,
        validators=[validate_roll_number],
        help_text="Enter in the format of THA079BEI042 or tha079bei042"
    )
    department = models.CharField(
        max_length=2,
        choices=Department.choices
    )
    current_semester = models.IntegerField(
        max_length=2,
        choices=Semester.choices,
        default=Semester.SEM_1
    )
    batch_year = models.PositiveIntegerField()
    section = models.CharField(
        max_length=5,
        choices=Section.choices,
        default=Section.GROUP_A  # for no section, group A is default
    )

    class Meta:
        indexes = [
            models.Index(fields=['id'])
        ]

    def __str__(self):
        return f"{self.roll_no} - {self.user.first_name}"


