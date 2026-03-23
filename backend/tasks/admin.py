from django.contrib import admin
from .models import Task, TaskRecord

class TaskRecordInline(admin.TabularInline):
    model = TaskRecord
    extra = 0
    readonly_fields = ('student', 'uploaded_file', 'submitted_at', 'marks_obtained', 'feedback', 'evaluated_at')
    can_delete = False

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_select_related = ('classroom', 'created_by')
    list_display = ('name', 'classroom', 'task_type', 'mode', 'status', 'full_marks', 'end_date', 'created_by')
    list_filter = ('status', 'task_type', 'mode', 'end_date', 'created_at')
    search_fields = ('name', 'classroom__name', 'created_by__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'end_date'
    inlines = [TaskRecordInline]

@admin.register(TaskRecord)
class TaskRecordAdmin(admin.ModelAdmin):
    list_select_related = ('task', 'student', 'task__classroom')
    list_display = ('task', 'student', 'submitted_at', 'marks_obtained', 'is_evaluated_display')
    list_filter = ('task__classroom', 'submitted_at')
    search_fields = ('task__name', 'student__username', 'student__email')
    readonly_fields = ('id', 'submitted_at')

    @admin.display(boolean=True, description='Evaluated')
    def is_evaluated_display(self, obj):
        return obj.is_evaluated
