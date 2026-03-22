from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, TeacherProfile, OTPToken

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_student', 'is_staff', 'is_active')
    list_filter = ('is_student', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role Configuration', {'fields': ('is_student',)}),
    )

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_select_related = ('user',)
    list_display = ('roll_no', 'get_username', 'get_email', 'department', 'current_semester', 'batch_year')
    list_filter = ('department', 'current_semester', 'batch_year')
    search_fields = ('roll_no', 'user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('id',)

    @admin.display(description='Username')
    def get_username(self, obj):
        return obj.user.username

    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.user.email

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_select_related = ('user',)
    list_display = ('get_username', 'department', 'designation', 'is_full_time', 'phone_number')
    list_filter = ('department', 'designation', 'is_full_time')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number')
    readonly_fields = ('id',)

    @admin.display(description='Username')
    def get_username(self, obj):
        return obj.user.username

@admin.register(OTPToken)
class OTPTokenAdmin(admin.ModelAdmin):
    list_select_related = ('user',)
    list_display = ('user', 'token', 'created_at', 'is_valid_display')
    search_fields = ('user__username', 'user__email')
    list_filter = ('created_at',)
    readonly_fields = ('id', 'created_at')

    @admin.display(boolean=True, description='Is Valid')
    def is_valid_display(self, obj):
        return obj.is_valid()
