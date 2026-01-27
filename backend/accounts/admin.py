from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import StudentProfile, TeacherProfile, User

admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(User)
