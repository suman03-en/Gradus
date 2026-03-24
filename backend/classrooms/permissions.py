from rest_framework import permissions


class HasJoinedOrIsCreator(permissions.BasePermission):
    """
    Grants Permission only if teacher is creator  or student has joined the specific classroom.
    """

    message = "Student enrolled in classroom or creator of classroom are only allowed."

    def has_object_permission(self, request, view, obj):
        if request.user.is_student:
            return obj.is_student_member(request.user)
        return obj.is_teacher(request.user)
