import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from .validators import validate_roll_number
from .constants import Semester, Department, Section, Designation


class User(AbstractUser):
    is_student = models.BooleanField(default=True)

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
        help_text="e.g THA079BEI042"
    )
    department = models.CharField(
        max_length=2,
        choices=Department.choices
    )
    current_semester = models.IntegerField(
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


class TeacherProfile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile"
    )
    department = models.CharField(
        max_length=2, 
        choices=Department.choices,
        blank=True,
        null=True
    )
    phone_number = models.CharField(max_length=10, blank=True)
    designation = models.CharField(
        max_length=10, 
        choices= Designation.choices,
        help_text="e.g. Assistant Professor, HOD")
    
    is_full_time = models.BooleanField(
        default=True,
        verbose_name="Full time"
        )

    class Meta:
        indexes = [models.Index(fields=["id"])]
    
    def __str__(self):
        return f"{self.user.username}"