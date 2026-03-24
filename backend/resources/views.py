from rest_framework import viewsets, mixins
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Resource
from .serializers import ResourceSerializer
from .permissions import HasResourcePermission
from django.contrib.contenttypes.models import ContentType


class ResourceViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for viewing and creating Resources attached to Classrooms or Tasks.
    """

    serializer_class = ResourceSerializer
    permission_classes = [HasResourcePermission]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Admin can see all, but basically we restrict by the query params for list
        user = self.request.user
        qs = Resource.objects.select_related("content_type", "uploaded_by").filter(
            scan_status=Resource.SCAN_STATUS_CLEAN
        )

        if self.action in ["retrieve", "destroy"]:
            return qs.order_by("-uploaded_at")

        # When listing, we expect content_type and object_id in query params
        ct_model = self.request.query_params.get("content_type")
        obj_id = self.request.query_params.get("object_id")

        if ct_model and obj_id:
            try:
                ct = ContentType.objects.get(model=ct_model)
                qs = qs.filter(content_type=ct, object_id=obj_id)
            except Exception:
                return Resource.objects.none()
        else:
            # If no params provided, only return resources uploaded by the user
            # (or none, depending on design. Returning only user's uploads is safer)
            qs = qs.filter(uploaded_by=user)

        return qs.order_by("-uploaded_at")

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
