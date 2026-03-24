from rest_framework import permissions


class IsTaskCreatorOrClassroomStudent(permissions.BasePermission):
    """
    Task permissions:
        - Read: student must be enrolled in classroom OR teacher must be task creator
        - Update/Delete: only task creator
    """

    message = "Student enrolled in classroom or creator of task are only allowed."

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

            # Teacher assigned in the classroom
            if obj.classroom.is_teacher(user):
                return True

            # Student who joined the classroom
            if user.is_student:
                return obj.classroom.is_student_member(user)

            return False

        # Classroom teachers can manage task content.
        return obj.classroom.is_teacher(user)


class CanViewTaskRecord(permissions.BasePermission):
    """Permission for viewing task records (submissions/evaluations)."""

    message = "Student who submitted task or creator of task can only view records."

    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return True

        if request.user.is_student:
            return obj.student == request.user

        return obj.task.classroom.is_teacher(request.user)


class IsTaskRecordOwner(permissions.BasePermission):
    """Only the student who owns the record can update it."""

    message = "Student who submitted the task can only perform this action."

    def has_object_permission(self, request, view, obj):
        return obj.student == request.user
