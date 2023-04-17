from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions
from rest_framework.exceptions import MethodNotAllowed

from .models import Photo
from .serializers import (
    PhotoCreateSerializer,
    PhotoDetailSerializer,
    PhotoPatchSerializer,
)


class PhotoViewSet(ModelViewSet):
    queryset = Photo.objects.all()
    http_method_names = [m for m in ModelViewSet.http_method_names if m != "put"]
    # serializer_class = PhotoCreateSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            permission_classes = [permissions.AllowAny]
        elif self.action in ("update", "partial_update", "destroy"):
            permission_classes = [IsAuthor]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "create":
            return PhotoCreateSerializer
        if self.action in ("list", "retrieve", "destroy"):
            return PhotoDetailSerializer
        if self.action == "partial_update":
            return PhotoPatchSerializer

    # def perform_update(self, serializer):
    #     inst = self.get_object()
    #     print()
    #     print(inst.title)
    #     print(inst.image.url)
    #     print()
    #     return super().perform_update(serializer)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class IsAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
