from rest_framework import permissions

class IsCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user

class IsStudent(permissions.BasePermission):
    message = "Student are only allowed."
    def has_permission(self, request, view):
        return request.user.is_student

class IsStudentOrReadOnly(permissions.BasePermission):
    message = "Students are only allowed to edit, update and delete."
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_student
    
class IsTeacherOrNotAllowed(permissions.BasePermission):
     message = "Teacher is only allowed. "
     def has_permission(self, request, view):
          return not request.user.is_student

class IsTeacherOrReadOnly(permissions.BasePermission):
    message = "Teacher is only allowed to edit, update and delete."
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return not request.user.is_student
    
    def has_object_permission(self, request, view, obj):
        """Grant permission for creating,updating and deleting task only to their owned objects"""
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return obj.created_by==request.user     