from django.contrib import admin
from .models import Task, TaskSubmission, TaskEvaluation

class TaskSubmissionInline(admin.TabularInline):
    model = TaskSubmission
    extra = 0
    readonly_fields = ('student', 'uploaded_file', 'submitted_at')
    can_delete = False

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_select_related = ('classroom', 'created_by')
    list_display = ('name', 'classroom', 'task_type', 'mode', 'status', 'full_marks', 'end_date', 'created_by')
    list_filter = ('status', 'task_type', 'mode', 'end_date', 'created_at')
    search_fields = ('name', 'classroom__name', 'created_by__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'end_date'
    inlines = [TaskSubmissionInline]

class TaskEvaluationInline(admin.StackedInline):
    model = TaskEvaluation
    extra = 0
    readonly_fields = ('id',)

@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_select_related = ('task', 'student', 'task__classroom')
    list_display = ('task', 'student', 'submitted_at', 'has_evaluation')
    list_filter = ('task__classroom', 'submitted_at')
    search_fields = ('task__name', 'student__username', 'student__email')
    readonly_fields = ('id', 'submitted_at')
    inlines = [TaskEvaluationInline]

    @admin.display(boolean=True, description='Evaluated')
    def has_evaluation(self, obj):
        return hasattr(obj, 'evaluations')

@admin.register(TaskEvaluation)
class TaskEvaluationAdmin(admin.ModelAdmin):
    list_select_related = ('submission__task', 'submission__student')
    list_display = ('get_task', 'get_student', 'marks_obtained', 'feedback_preview')
    search_fields = ('submission__task__name', 'submission__student__username')
    readonly_fields = ('id',)

    @admin.display(description='Task')
    def get_task(self, obj):
        return obj.submission.task.name

    @admin.display(description='Student')
    def get_student(self, obj):
        return obj.submission.student.username

    @admin.display(description='Feedback')
    def feedback_preview(self, obj):
        return obj.feedback[:50] + '...' if len(obj.feedback) > 50 else obj.feedback
