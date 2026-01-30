from django.db import models


class TaskStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"

class TaskMode(models.TextChoices):
    ONLINE = "online", "Online"
    OFFLINE = "offline", "Offline"

class TaskType(models.TextChoices):
    ASSIGNMENT = "assignment", "Assignment"
    ASSESSMENT = "assessment", "Assessment"
    LAB_REPORT = "lab_report", "Lab Report"
    QUIZ = "quiz", "Quiz"