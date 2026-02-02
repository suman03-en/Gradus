from rest_framework import permissions


class IsTaskCreatorOrClassroomStudent(permissions.BasePermission):
    """
    Task permissions:
        - Read: student must be enrolled in classroom OR teacher must be task creator
        - Update/Delete: only task creator
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return not request.user.is_student

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            # Teacher who created the task
            if obj.created_by == user:
                return True

            # Student who joined the classroom
            if user.is_student:
                return obj.classroom.students.filter(id=user.id).exists()

            return False

        # Only task creator can update/delete
        return obj.created_by == user
    
class IsStudentForWrite(permissions.BasePermission):
    message = "Only students can submit or modify task submissions."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_student
    
class CanViewSubmission(permissions.BasePermission):
    message = "You do not have permission to view this submission."

    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return True

        if request.user.is_student:
            return obj.student == request.user

        return obj.task.created_by == request.user
        