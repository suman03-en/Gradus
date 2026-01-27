import uuid
from django.db import models
from django.conf import settings
from .utils import generate_classroom_code

class Classroom(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_classrooms",
    )
    invite_code = models.CharField(max_length=10, unique=True, editable=False)
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="joined_classrooms",
        blank=True
    )
    is_active = models.BooleanField(default=True) #set is_active to False when deleting
    created_at = models.DateTimeField(auto_now_add=True)

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
            self.invite_code=new_code
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Subject(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100)
    group = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="subjects"
    )

    def __str__(self):
        return self.name

