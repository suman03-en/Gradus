from rest_framework import permissions

class IsTeacherOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        return not request.user.is_student
    
class HasJoinedOrIsCreator(permissions.BasePermission):
    """
    Grants Permission only if teacher is creator  or student has joined the specific classroom.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_student:
            return obj.students.filter(id=request.user.id).exists()
        return obj.created_by == request.user