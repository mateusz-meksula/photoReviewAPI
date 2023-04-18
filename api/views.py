from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions

from .models import Photo
from .serializers import (
    PhotoCreateSerializer,
    PhotoDetailSerializer,
    PhotoPatchSerializer,
)


class PhotoViewSet(ModelViewSet):
    """
    ViewSet for Photo instances management.
    """

    queryset = Photo.objects.all()

    # exclude `put` HTTP method
    http_method_names = [m for m in ModelViewSet.http_method_names if m != "put"]

    def get_permissions(self):
        """
        Set permission depending on the action.
        """

        if self.action in ("list", "retrieve"):
            permission_classes = [permissions.AllowAny]
        elif self.action in ("update", "partial_update", "destroy"):
            permission_classes = [IsAuthor]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Set serializer class depending on the action.
        """

        if self.action == "create":
            return PhotoCreateSerializer
        if self.action in ("list", "retrieve", "destroy"):
            return PhotoDetailSerializer
        if self.action == "partial_update":
            return PhotoPatchSerializer

    def perform_create(self, serializer):
        """
        Assigns authenticated user to the photo instance.
        """
        serializer.save(author=self.request.user)


class IsAuthor(permissions.BasePermission):
    """
    Grants author object permission.
    """

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
