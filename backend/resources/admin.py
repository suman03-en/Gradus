from django.contrib import admin
from django.utils.html import format_html
from .models import Resource

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_select_related = ('uploaded_by', 'content_type')
    list_display = ('name', 'uploaded_by', 'content_type', 'object_id', 'uploaded_at', 'file_link')
    list_filter = ('content_type', 'uploaded_at')
    search_fields = ('name', 'uploaded_by__username', 'object_id')
    readonly_fields = ('id', 'uploaded_at')
    date_hierarchy = 'uploaded_at'

    @admin.display(description='File View')
    def file_link(self, obj):
        if obj.file:
            return format_html("<a href='{}' target='_blank'>View File</a>", obj.file.url)
        return "No File"
