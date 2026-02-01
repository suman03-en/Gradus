from rest_framework import permissions


class IsTaskCreatorOrClassroomStudent(permissions.BasePermission):
    """
    Task permissions:
        - Read: student must be enrolled in classroom OR teacher must be task creator
        - Update/Delete: only task creator
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        print(obj.created_by)
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
        