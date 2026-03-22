from django.contrib import admin
from .models import Classroom

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'invite_code', 'is_active', 'created_at', 'student_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'invite_code', 'created_by__username', 'created_by__email')
    readonly_fields = ('id', 'invite_code', 'created_at')
    filter_horizontal = ('students',)
    date_hierarchy = 'created_at'

    @admin.display(description='Enrolled Students', ordering='students_count')
    def student_count(self, obj):
        return obj.students_count

    def get_queryset(self, request):
        from django.db.models import Count
        qs = super().get_queryset(request)
        return qs.select_related('created_by').annotate(students_count=Count('students'))