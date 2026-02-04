import uuid
import secrets
import string
from datetime import datetime, timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from .validators import validate_roll_number, phone_regex
from .constants import Semester, Department, Section, Designation


class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    is_student = models.BooleanField(default=True, verbose_name="Are you a student?")

class StudentProfile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )
    roll_no = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
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
    batch_year = models.PositiveIntegerField(null=True, blank=True)
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
    phone_number = models.CharField(
        validators=[phone_regex, ],
        blank=True)
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

class OTPToken(models.Model):
    """
    Class used to store the token for the password reset
    """
    id = models.UUIDField(
        primary_key=True,
        default= uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token'
    )
    token = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)

    
    def is_valid(self):
        token_lifespan = 5 * 60  # min
        now = datetime.now(timezone.utc)
        time_diff = now - self.created_at
        time_diff = time_diff.total_seconds()
        if time_diff >= token_lifespan:
            return False
        return True
    
    def set_password(self, password):
        self.user.set_password(password)
        self.user.save()

    @staticmethod
    def generate_token(length):
        token = "".join(secrets.choice(string.digits) for _ in range(length))
        return token



