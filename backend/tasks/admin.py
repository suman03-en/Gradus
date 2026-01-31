from django.contrib import admin
from .models import Task, TaskSubmission, TaskEvaluation

admin.site.register(Task)
admin.site.register(TaskSubmission)
admin.site.register(TaskEvaluation)
