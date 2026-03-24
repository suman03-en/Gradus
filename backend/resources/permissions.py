from rest_framework import permissions
from classrooms.models import Classroom
from tasks.models import Task
from django.contrib.contenttypes.models import ContentType


class HasResourcePermission(permissions.BasePermission):
    """
    Custom permission to ensure user can access/modify the resource.
    - Creators of Classroom/Task can do anything.
    - Students enrolled in Classroom/Task can view (GET).
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # For list/create, we check query params or request data
        if view.action in ["list", "create"]:
            if view.action == "list":
                content_type_model = request.query_params.get("content_type")
                object_id = request.query_params.get("object_id")
            else:
                content_type_model = request.data.get("content_type")
                object_id = request.data.get("object_id")

            # If these are missing or invalid, allow the view/serializer to handle it
            # (they will return an empty list or a 400 Bad Request respectively)
            if not content_type_model or not object_id:
                return True

            try:
                ct = ContentType.objects.get(model=content_type_model)
                obj = ct.get_object_for_this_type(id=object_id)
            except Exception:
                return True

            return self._check_object_permission(request, obj, view.action)

        return True

    def has_object_permission(self, request, view, obj):
        return self._check_object_permission(request, obj.content_object, view.action)

    def _check_object_permission(self, request, target_obj, action):
        user = request.user

        if isinstance(target_obj, Classroom):
            is_creator = target_obj.is_teacher(user)
            is_student = target_obj.is_student_member(user)
        elif isinstance(target_obj, Task):
            is_creator = target_obj.classroom.is_teacher(user)
            is_student = target_obj.classroom.is_student_member(user)
        else:
            return False

        if action in ["list", "retrieve"]:
            return is_creator or is_student

        # for create, update, destroy
        return is_creator
