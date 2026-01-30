from django.contrib import admin
from .models import Classroom, Subject

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    readonly_fields = ('invite_code',)
    
admin.site.register(Subject)